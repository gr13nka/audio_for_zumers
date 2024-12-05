import os
from telegram.request import HTTPXRequest
import subprocess
import random
import wave
from vosk import Model, KaldiRecognizer
import json
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)

# Путь к директориям
VIDEO_DIR = "videos"  # Папка с паркур-видео
TEMP_DIR = "temp"  # Папка для временных файлов
MODEL_DIR = "model"  # Папка с Vosk-моделью

# Убедитесь, что временная папка существует
os.makedirs(TEMP_DIR, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработка команды /start.
    """
    await update.message.reply_text(
        "Привет! Отправь мне голосовое сообщение, и я создам видео с паркуром и текстом из твоего сообщения."
    )

def generate_subtitles(audio_path: str, recognized_text: str, subtitle_path: str) -> None:
    """
    Создаёт файл субтитров (.srt) с синхронизацией текста.
    
    :param audio_path: Путь к аудиофайлу для анализа.
    :param recognized_text: Полный распознанный текст.
    :param subtitle_path: Путь для сохранения файла субтитров.
    """
    model = Model(MODEL_DIR)
    wf = wave.open(audio_path, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    subtitles = []
    index = 1

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            for word in result.get("result", []):
                start_time = word["start"]
                end_time = word["end"]
                text = word["word"]
                subtitles.append(f"{index}\n{format_time(start_time)} --> {format_time(end_time)}\n{text}\n")
                index += 1

    wf.close()

    # Сохраняем субтитры в .srt файл
    with open(subtitle_path, "w", encoding="utf-8") as srt_file:
        srt_file.writelines(subtitles)

def replace_audio(video_path: str, audio_path: str, output_path: str) -> None:
    """
    Заменяет аудиодорожку в видео.
    
    :param video_path: Путь к исходному видео.
    :param audio_path: Путь к новой аудиодорожке.
    :param output_path: Путь для сохранения результата.
    """
    subprocess.run([
        'ffmpeg', '-i', video_path, '-i', audio_path, '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0',
        '-shortest', output_path
    ], check=True)

def format_time(seconds: float) -> str:
    """
    Форматирует время в формате SRT (чч:мм:сс,мс).
    
    :param seconds: Время в секундах.
    :return: Форматированное время.
    """
    millis = int((seconds % 1) * 1000)
    secs = int(seconds)
    mins = secs // 60
    hrs = mins // 60
    return f"{hrs:02}:{mins % 60:02}:{secs % 60:02},{millis:03}"

def trim_video(video_path: str, output_path: str, duration: float) -> None:
    """
    Обрезает видео до заданной длительности.
    
    :param video_path: Путь к исходному видео.
    :param output_path: Путь для сохранения обрезанного видео.
    :param duration: Длительность обрезанного видео в секундах.
    """
    subprocess.run([
        'ffmpeg', '-i', video_path, '-t', str(duration), '-c:v', 'libx264', '-c:a', 'aac', output_path
    ], check=True)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработка голосового сообщения.
    """
    try:
        # Скачиваем голосовое сообщение
        voice_file = await update.message.voice.get_file()
        voice_path = os.path.join(TEMP_DIR, f"voice_{update.message.chat_id}.ogg")
        audio_path = os.path.join(TEMP_DIR, f"audio_{update.message.chat_id}.wav")
        await voice_file.download_to_drive(voice_path)

        # Конвертируем голосовое сообщение в WAV для Vosk
        subprocess.run(['ffmpeg', '-i', voice_path, '-ar', '16000', '-ac', '1', audio_path], check=True)

        # Распознаем текст из голосового сообщения
        recognized_text = transcribe_audio(audio_path)
        if not recognized_text.strip():
            await update.message.reply_text("Не удалось распознать текст. Попробуй снова.")
            return

        # Генерация субтитров
        subtitle_path = os.path.join(TEMP_DIR, f"subtitles_{update.message.chat_id}.srt")
        generate_subtitles(audio_path, recognized_text, subtitle_path)

        # Выбираем случайное видео из папки
        video_path = random.choice([os.path.join(VIDEO_DIR, f) for f in os.listdir(VIDEO_DIR)])
        trimmed_video_path = os.path.join(TEMP_DIR, f"trimmed_{update.message.chat_id}.mp4")
        video_with_audio_path = os.path.join(TEMP_DIR, f"video_audio_{update.message.chat_id}.mp4")
        output_path = os.path.join(TEMP_DIR, f"output_{update.message.chat_id}.mp4")

        # Обрезаем видео до длины голосового сообщения
        voice_duration = update.message.voice.duration  # Длительность голосового сообщения в секундах
        trim_video(video_path, trimmed_video_path, voice_duration)

        # Заменяем звуковую дорожку
        replace_audio(trimmed_video_path, audio_path, video_with_audio_path)

        # Накладываем субтитры на видео
        subprocess.run([
            'ffmpeg', '-i', video_with_audio_path, '-vf', f"subtitles={subtitle_path}:force_style='FontSize=24'",
            '-c:a', 'copy', output_path
        ], check=True)

        # Отправляем готовое видео пользователю
        with open(output_path, 'rb') as video:
            await update.message.reply_video(video=video, caption="Готово!")

    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"Ошибка обработки видео: {e}")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {e}")
    finally:
        # Удаляем временные файлы
        clean_temp_files(update.message.chat_id)

def transcribe_audio(audio_path: str) -> str:
    """
    Распознает текст из аудиофайла с помощью Vosk.
    """
    model = Model(MODEL_DIR)
    wf = wave.open(audio_path, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    text_result = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text_result.append(result.get("text", ""))

    wf.close()
    return " ".join(text_result)


def add_text_to_video(video_path: str, output_path: str, text: str) -> None:
    """
    Добавляет текст поверх видео с помощью ffmpeg.
    """
    # Убираем опасные символы
    text_safe = text.replace("'", "\\'").replace('"', '\\"')

    # Формируем фильтр drawtext
    drawtext_filter = f"drawtext=text='{text_safe}':fontcolor=white:fontsize=24:x=(w-text_w)/2:y=h-50"

    # Запускаем ffmpeg
    subprocess.run([
        'ffmpeg', '-i', video_path, '-vf', drawtext_filter, '-codec:a', 'copy', output_path
    ], check=True)


def clean_temp_files(chat_id: int) -> None:
    """
    Удаляет временные файлы для конкретного чата.
    """
    for file in os.listdir(TEMP_DIR):
        if str(chat_id) in file:
            try:
                os.remove(os.path.join(TEMP_DIR, file))
            except FileNotFoundError:
                pass


def main():
    """
    Основная функция для запуска бота.
    """
    # Создаём приложение
    request = HTTPXRequest(connect_timeout=60.0, read_timeout=60.0)

    application = Application.builder().token("7872793386:AAEVh1YUgrAOdhi9NjBvpzUcyO80Mz-dVfg").request(request).build()
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Запускаем приложение
    application.run_polling()


if __name__ == "__main__":
    main()


