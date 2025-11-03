import asyncio
import os
import shutil
import zipfile
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# ---------- CONFIGURAÇÃO (ajuste para seu ambiente) ----------
BUNDLETOOL_JAR = r"C:\Users\salle\Downloads\bundletool-all-1.18.2.jar"
KEYSTORE_PATH = r"C:\Users\salle\Downloads\meu-keystore.jks"
KEYSTORE_PASS = "Sales1226"
KEY_ALIAS = "meu-alias"
KEY_PASS = "Sales1226"

# tamanho máximo aceito (bytes) - 200MB por padrão
MAX_UPLOAD_SIZE = 200 * 1024 * 1024

# pasta temporária root (padrão /tmp no linux, usa tempdir do sistema)
TMP_ROOT = None  # None -> usa tempfile.TemporaryDirectory()
# --------------------------------------------------------------

app = FastAPI(title="AAB → APK Generator (FastAPI)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restringir em produção
    allow_methods=["*"],
    allow_headers=["*"],
)

async def run_command(cmd: list, cwd: str = None, timeout: int = 600):
    """Roda comando async e captura saída. Timeout em segundos."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise HTTPException(status_code=500, detail="Processo demorou demais e foi finalizado (timeout).")
    if proc.returncode != 0:
        out = (stdout or b"").decode(errors="ignore")
        err = (stderr or b"").decode(errors="ignore")
        raise HTTPException(status_code=500, detail=f"Erro no bundletool (code {proc.returncode}). stderr: {err}\nstdout: {out}")
    return (stdout or b"").decode(errors="ignore"), (stderr or b"").decode(errors="ignore")

def find_universal_apk(extract_dir: Path):
    """Procura recursivamente por 'universal.apk' e retorna Path ou None."""
    print(f"Procurando APK em: {extract_dir}")
    
    # Lista todos os arquivos para debug
    all_files = []
    for p in extract_dir.rglob("*"):
        if p.is_file():
            all_files.append(str(p))
            print(f"Arquivo encontrado: {p}")
    
    # Procura por universal.apk (exato)
    for p in extract_dir.rglob("universal.apk"):
        print(f"Encontrou universal.apk: {p}")
        return p
    
    # Procura por qualquer .apk
    apk_files = []
    for p in extract_dir.rglob("*.apk"):
        apk_files.append(p)
        print(f"Arquivo APK encontrado: {p}")
    
    # Se encontrou apenas um APK, usa ele
    if len(apk_files) == 1:
        print(f"Usando único APK encontrado: {apk_files[0]}")
        return apk_files[0]
    
    # Se encontrou múltiplos APKs, prefere o que tem "universal" no nome
    for apk in apk_files:
        if "universal" in apk.name.lower():
            print(f"Usando APK universal: {apk}")
            return apk
    
    # Se ainda não encontrou, usa o primeiro APK disponível
    if apk_files:
        print(f"Usando primeiro APK disponível: {apk_files[0]}")
        return apk_files[0]
    
    print("Nenhum arquivo APK encontrado!")
    return None

@app.get("/", response_class=HTMLResponse)
def index():
    # página simples para enviar .aab
    return HTMLResponse(content=open(Path(__file__).parent / "index.html", "r", encoding="utf-8").read())

@app.post("/generate-apk")
async def generate_apk(aab: UploadFile = File(...)):
    print(f"Recebido arquivo: {aab.filename}")
    
    # valida extensão
    if not aab.filename.lower().endswith(".aab"):
        raise HTTPException(status_code=400, detail="Arquivo precisa ter extensão .aab")

    # cria temp dir por requisição
    tmpdir_obj = tempfile.TemporaryDirectory(dir=TMP_ROOT)
    tmpdir = Path(tmpdir_obj.name)
    print(f"Diretório temporário criado: {tmpdir}")
    
    try:
        aab_path = tmpdir / "upload.aab"
        print(f"Salvando arquivo em: {aab_path}")
        
        # salvar arquivo no disco
        with aab_path.open("wb") as f:
            total = 0
            while True:
                chunk = await aab.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_SIZE:
                    raise HTTPException(status_code=400, detail=f"Arquivo excede o limite de {MAX_UPLOAD_SIZE} bytes.")
                f.write(chunk)
        
        print(f"Arquivo salvo com {total} bytes")

        # caminhos de saída
        apks_path = tmpdir / "output.apks"
        extract_dir = tmpdir / "extracted"

        # comando bundletool build-apks --mode=universal ...
        cmd = [
            "java",
            "-jar",
            str(BUNDLETOOL_JAR),
            "build-apks",
            f"--bundle={str(aab_path)}",
            f"--output={str(apks_path)}",
            "--mode=universal",
            f"--ks={str(KEYSTORE_PATH)}",
            f"--ks-pass=pass:{KEYSTORE_PASS}",
            f"--ks-key-alias={KEY_ALIAS}",
            f"--key-pass=pass:{KEY_PASS}"
        ]

        print(f"Executando comando: {' '.join(cmd)}")
        
        # executa bundletool (timeout generoso)
        stdout, stderr = await run_command(cmd, cwd=str(tmpdir), timeout=900)
        print(f"Bundletool stdout: {stdout}")
        print(f"Bundletool stderr: {stderr}")

        # Verifica se o arquivo .apks foi criado
        if not apks_path.exists():
            raise HTTPException(status_code=500, detail=f"Arquivo .apks não foi gerado: {apks_path}")
        
        print(f"Arquivo .apks criado: {apks_path} ({apks_path.stat().st_size} bytes)")

        # extrai o apks (é um zip)
        extract_dir.mkdir(exist_ok=True)
        print(f"Extraindo {apks_path} para {extract_dir}")
        
        with zipfile.ZipFile(str(apks_path), 'r') as z:
            print(f"Conteúdo do .apks: {z.namelist()}")
            z.extractall(path=str(extract_dir))

        # procura o universal.apk
        apk_path = find_universal_apk(extract_dir)
        if not apk_path:
            raise HTTPException(status_code=500, detail="Nenhum arquivo APK encontrado dentro do .apks gerado.")

        # Verifica se o arquivo realmente existe antes de retornar
        if not apk_path.exists():
            raise HTTPException(status_code=500, detail=f"Arquivo APK não existe: {apk_path}")

        print(f"APK encontrado: {apk_path} ({apk_path.stat().st_size} bytes)")

        # Copia o APK para um arquivo temporário que não será deletado imediatamente
        final_apk = tempfile.NamedTemporaryFile(suffix=".apk", delete=False)
        final_apk_path = Path(final_apk.name)
        final_apk.close()
        
        shutil.copy2(str(apk_path), str(final_apk_path))
        print(f"APK copiado para: {final_apk_path}")

        # retorna o APK como download (attachment). Nome do arquivo baseado no original .aab
        out_name = f"{aab.filename.rsplit('.aab', 1)[0]}.apk"
        print(f"Retornando APK como: {out_name}")
        
        # Retorna FileResponse que vai deletar o arquivo após o download
        return FileResponse(
            path=str(final_apk_path), 
            filename=out_name, 
            media_type="application/vnd.android.package-archive",
            background=lambda: os.unlink(final_apk_path)  # deleta após o download
        )
    
    except Exception as e:
        print(f"Erro durante o processamento: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # cleanup automático quando tmpdir_obj for garbage-collected, mas forçamos remoção
        try:
            tmpdir_obj.cleanup()
            print(f"Diretório temporário limpo: {tmpdir}")
        except Exception as e:
            print(f"Erro ao limpar arquivos temporários: {e}")