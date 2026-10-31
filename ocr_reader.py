"""Local OCR. Image bytes and recognized text never leave this computer."""
import io

_engine = None

def group_lines(boxes, texts):
    pieces = []
    for box, text in zip(boxes, texts):
        xs, ys = [float(p[0]) for p in box], [float(p[1]) for p in box]
        pieces.append((sum(ys)/4, min(xs), max(ys)-min(ys), text))
    groups = []
    for y, x, height, text in sorted(pieces):
        if not groups or abs(y - groups[-1]['y']) > max(6, min(height, groups[-1]['height']) * .5):
            groups.append({'y': y, 'height': height, 'parts': []})
        groups[-1]['parts'].append((x, text))
    return '\n'.join(' '.join(text for _, text in sorted(group['parts'])) for group in groups)

def read_image_text(raw):
    global _engine
    try:
        from PIL import Image, ImageOps
        from rapidocr import RapidOCR
    except ImportError:
        raise ValueError('Instale as dependências atualizadas para ler imagens: python -m pip install -r requirements.txt')
    try:
        with Image.open(io.BytesIO(raw)) as source:
            if source.width * source.height > 25_000_000:
                raise ValueError('A imagem deve ter no máximo 25 megapixels.')
            if source.format not in ['PNG', 'JPEG', 'WEBP']:
                raise ValueError('Use uma imagem PNG, JPG ou WebP.')
            image = ImageOps.exif_transpose(source).convert('RGB')
    except ValueError:
        raise
    except Exception:
        raise ValueError('Não foi possível abrir essa imagem. Use PNG, JPG ou WebP.')
    try:
        if _engine is None:
            _engine = RapidOCR()
        result = _engine(image)
        if result.txts is None or result.boxes is None:
            raise ValueError('Nenhum texto foi reconhecido na imagem.')
        return group_lines(result.boxes, result.txts)
    except ValueError:
        raise
    except Exception:
        raise ValueError('O leitor de imagens não conseguiu concluir. Confira a instalação e tente uma imagem mais nítida. No primeiro uso pode ser necessário baixar os modelos de leitura.')
