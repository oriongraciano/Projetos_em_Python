import os
import sys
import json
import re
import warnings

warnings.filterwarnings("ignore")

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['DNNL_MAX_CPU_ISA'] = 'SSE41'
os.environ['ONEDNN_MAX_CPU_ISA'] = 'SSE41'

try:
    import torch
    from pdf2image import convert_from_path
    from PIL import ImageEnhance, Image, ImageOps, ImageFilter
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel

except ImportError as e:
    print(json.dumps({
        'erro': f'Dependência faltando: {str(e)}'
    }))
    sys.exit(1)

torch.backends.mkldnn.enabled = False

device = "cpu"
torch.set_num_threads(2)

MODEL_NAME = "microsoft/trocr-base-handwritten"

processor = TrOCRProcessor.from_pretrained(
    MODEL_NAME,
    use_fast=True
)

model = VisionEncoderDecoderModel.from_pretrained(
    MODEL_NAME
).to(device)

POPPLER_PATH = r'C:\poppler\Library\bin'
TEMP_DEBUG_DIR = r'C:\temp'


def preprocessar_para_ocr(imagem):
    """
    Pré-processamento otimizado para OCR manuscrito.
    """

    imagem = imagem.convert('L').filter(ImageFilter.SHARPEN)

    enhancer = ImageEnhance.Contrast(imagem)
    imagem = enhancer.enhance(4.0)

    imagem = imagem.point(
        lambda x: 0 if x < 140 else 255,
        '1'
    )

    return imagem.convert('RGB')


def extrair_com_deep_learning(arquivo_path):
    try:

        images = convert_from_path(
            arquivo_path,
            first_page=1,
            last_page=1,
            poppler_path=POPPLER_PATH,
            dpi=450
        )

        img = images[0]

        w, h = img.size

        area_recorte = (
            0,
            int(h * 0.96),
            int(w * 0.30),
            h
        )

        canto_inferior = img.crop(area_recorte)

        canto_preparado = preprocessar_para_ocr(
            canto_inferior
        )

        if not os.path.exists(TEMP_DEBUG_DIR):
            os.makedirs(TEMP_DEBUG_DIR)

        canto_preparado.save(
            os.path.join(
                TEMP_DEBUG_DIR,
                'debug_ocr_binarizado.png'
            )
        )

        pixel_values = processor(
            canto_preparado,
            return_tensors="pt"
        ).pixel_values.to(device)

        with torch.no_grad():

            generated_ids = model.generate(
                pixel_values,
                num_beams=10,
                max_new_tokens=30,
                early_stopping=False,
                length_penalty=1.5
            )

        texto_bruto = processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0]

        texto_limpo = re.sub(
            r'[^0-9\-]',
            '',
            texto_bruto
        )

        match = re.search(
            r'(\d+-\d+)',
            texto_limpo
        )

        return match.group(1) if match else texto_limpo

    except Exception as e:
        raise Exception(
            f"Erro na extração: {str(e)}"
        )


def processar_e_responder(arquivo_path):

    if not os.path.exists(arquivo_path):

        print(json.dumps({
            'sucesso': False,
            'erro': 'Arquivo não encontrado'
        }))

        return

    try:

        resultado = extrair_com_deep_learning(
            arquivo_path
        )

        if (
            resultado
            and "-" in resultado
            and len(resultado) >= 3
        ):

            nome_seguro = re.sub(
                r'[\\/*?:"<>|]',
                '',
                resultado
            ).strip()

            print(json.dumps({
                'sucesso': True,
                'numero_processo': nome_seguro,
                'novo_nome': f"{nome_seguro}.pdf",
                'metodo': 'OCR_Binarized_Deep_Search'
            }, ensure_ascii=False))

        else:

            print(json.dumps({
                'sucesso': False,
                'erro': 'Leitura inconsistente ou incompleta',
                'lido': resultado
            }))

    except Exception as e:

        print(json.dumps({
            'sucesso': False,
            'erro': str(e)
        }))


if __name__ == '__main__':

    if len(sys.argv) > 1:
        processar_e_responder(sys.argv[1])