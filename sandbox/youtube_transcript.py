"""
Modulo YouTube Transcript para Web Learn v2
Integra youtube_transcript_api (v1.2.4+) no pipeline de aprendizado.

Uso:
    from youtube_transcript import extrair_youtube_transcript
    texto = extrair_youtube_transcript("https://www.youtube.com/watch?v=...")
"""
import re
import logging

logger = logging.getLogger('web_learn.yt')

def extrair_video_id(url: str) -> str | None:
    """Extrai o video_id de URLs do YouTube."""
    # youtube.com/watch?v=VIDEO_ID
    m = re.search(r'(?:v=)([0-9A-Za-z_-]{11})', url)
    if m:
        return m.group(1)
    # youtu.be/VIDEO_ID
    m = re.search(r'youtu\.be/([0-9A-Za-z_-]{11})', url)
    if m:
        return m.group(1)
    # youtube.com/embed/VIDEO_ID
    m = re.search(r'(?:embed/)([0-9A-Za-z_-]{11})', url)
    if m:
        return m.group(1)
    return None

def extrair_youtube_transcript(url: str) -> str | None:
    """
    Baixa a transcricao de um video do YouTube.
    Retorna o texto concatenado ou None se falhar.
    """
    video_id = extrair_video_id(url)
    if not video_id:
        logger.warning(f'URL do YouTube invalida: {url[:80]}')
        return None
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        
        if not transcript:
            logger.warning(f'Transcricao vazia para {video_id}')
            return None
        
        # Concatenar texto (API v1.2.4 retorna objetos com .text)
        if hasattr(transcript[0], 'get'):
            texto = ' '.join([seg.get('text', '') for seg in transcript])
        else:
            texto = ' '.join([seg.text for seg in transcript])
        logger.info(f'YouTube OK: {video_id} -> {len(texto)} chars, {len(transcript)} segmentos')
        return texto
        
    except Exception as e:
        erro_msg = str(e)
        # Extrair causa especifica, se disponivel
        if 'Subtitles are disabled' in erro_msg:
            logger.warning(f'YouTube {video_id}: legendas desabilitadas para este video')
        elif 'No transcript found' in erro_msg:
            logger.warning(f'YouTube {video_id}: nenhuma transcricao disponivel nos idiomas solicitados')
        else:
            logger.warning(f'YouTube {video_id}: {erro_msg[:100]}')
        return None

def detectar_youtube(url: str) -> bool:
    """Verifica se a URL e do YouTube."""
    return bool(re.search(r'(youtube\.com|youtu\.be)', url))


if __name__ == '__main__':
    # Teste
    logging.basicConfig(level=logging.INFO)
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore
    url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    texto = extrair_youtube_transcript(url)
    if texto:
        print(f'OK! {len(texto)} chars extraidos')
        safe = texto[:200].encode('utf-8', errors='replace').decode('utf-8')
        print(f'Primeiros 200 chars: {safe}')
    else:
        print('Falha ao extrair transcricao')
