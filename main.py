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
import platform
import os
import platform
import glob

# Путь к директориям
VIDEO_DIR = "videos"  # Папка с паркур-видео
TEMP_DIR = "temp"  # Папка для временных файлов
MODEL_DIR = "model"  # Папка с Vosk-моделью по умолчанию там маленькая, но можно скачать поумнее вот тут https://alphacephei.com/vosk/models архив распаковать и положить в папку
YOUR_BOT_TOKEN = "7872793386:AAEVh1YUgrAOdhi9NjBvpzUcyO80Mz-dVfg"

# Безопасность - только авторизованные пользователи могут использовать бота
AUTHORIZED_USER_ID = 332605674  # ID владельца бота
# Убедитесь, что временная папка существует
os.makedirs(TEMP_DIR, exist_ok=True)

  

def find_ffmpeg_bin():
    # Ищем папки с ffmpeg в ./ffmpeg/
    ffmpeg_dirs = glob.glob("./ffmpeg/ffmpeg-*-essentials_build/bin/ffmpeg.exe")
    if ffmpeg_dirs:
        # Берём первый найденный файл (обычно будет один)
        print("ffmpeg succesfuly found!")
        return os.path.normpath(ffmpeg_dirs[0])
    else:
        raise FileNotFoundError("ffmpeg.exe не найден. Проверьте, что он есть в ./ffmpeg/ffmpeg-*/bin/")


def is_user_authorized(user_id: int) -> bool:
    """
    Проверяет, авторизован ли пользователь для использования бота.
    
    :param user_id: ID пользователя Telegram.
    :return: True, если пользователь авторизован, иначе False.
    """
    return user_id == AUTHORIZED_USER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработка команды /start.
    """
    user_id = update.effective_user.id
    
    if is_user_authorized(user_id):
        await update.message.reply_text(
            "Привет! Отправь мне голосовое сообщение, и я создам видео с паркуром и текстом из твоего сообщения."
        )
    else:
        await update.message.reply_text(
            "Извините, у вас нет доступа к этому боту. Он предназначен только для личного использования."
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
    print("subtitles created")
    # Сохраняем субтитры в .srt файл
    with open(subtitle_path, "w", encoding="utf-8") as srt_file:
        srt_file.writelines(subtitles)
        print("subtitles written to file")

def replace_audio(video_path: str, audio_path: str, output_path: str) -> None:
    """
    Заменяет аудиодорожку в видео.
    
    :param video_path: Путь к исходному видео.
    :param audio_path: Путь к новой аудиодорожке.
    :param output_path: Путь для сохранения результата.
    """
    subprocess.run([
        ffmpeg_cmd, '-i', video_path, '-i', audio_path, '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0',
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
        ffmpeg_cmd, '-i', video_path, '-t', str(duration), '-c:v', 'libx264', '-c:a', 'aac', output_path
    ], check=True)

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
    print("text Recognized", text_result)
    return " ".join(text_result)


def normalize_path(path: str) -> str:
    """
    Normalizes the path for use with FFmpeg, ensuring compatibility on Windows.
    Converts backslashes to forward slashes if running on Windows.

    :param path: The original file path.
    :return: The normalized path.
    """
    if platform.system() == "Windows":
        return os.path.normpath(path).replace("\\", "/")
    return os.path.normpath(path)


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
        ffmpeg_cmd, '-i', video_path, '-vf', drawtext_filter, '-codec:a', 'copy', output_path
    ], check=True)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработка голосового сообщения.
    """
    user_id = update.effective_user.id
    
    # Проверяем, авторизован ли пользователь
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "Извините, у вас нет доступа к этому боту. Он предназначен только для личного использования."
        )
        print(f"Unauthorized access attempt from user ID: {user_id}")
        return
        
    try:
        # Log start of processing
        print("Started processing voice message...")

        # Скачиваем голосовое сообщение
        voice_file = await update.message.voice.get_file()
        voice_path = os.path.join(TEMP_DIR, f"voice_{update.message.chat_id}.ogg")
        audio_path = os.path.join(TEMP_DIR, f"audio_{update.message.chat_id}.wav")

        print(f"Downloading voice message to {voice_path}...")
        await voice_file.download_to_drive(voice_path)
        print("Download complete.")

        # Конвертируем голосовое сообщение в WAV для Vosk
        print("Converting voice message to WAV format...")
        subprocess.run([ffmpeg_cmd, '-y', '-i', voice_path, '-ar', '16000', '-ac', '1', audio_path], check=True)
        print("Conversion complete.")

        # Распознаем текст из голосового сообщения
        print("===Transcribing audio...")
        recognized_text = transcribe_audio(audio_path)
        print(f"===Recognized text: {recognized_text}")

        if not recognized_text.strip():
            await update.message.reply_text("Не удалось распознать текст.")
            recognized_text = " "

        # Генерация субтитров
        subtitle_path = os.path.join(TEMP_DIR, f"subtitles_{update.message.chat_id}.srt")
        print("===Generating subtitles...")
        generate_subtitles(audio_path, recognized_text, subtitle_path)
        print(f"Subtitles saved to {subtitle_path}.")

        # Выбираем случайное видео из папки
        print("===Selecting random video...")
        video_path = random.choice([os.path.join(VIDEO_DIR, f) for f in os.listdir(VIDEO_DIR)])
        trimmed_video_path = os.path.join(TEMP_DIR, f"trimmed_{update.message.chat_id}.mp4")
        video_with_audio_path = os.path.join(TEMP_DIR, f"video_audio_{update.message.chat_id}.mp4")
        output_path = os.path.join(TEMP_DIR, f"output_{update.message.chat_id}.mp4")

        # Обрезаем видео до длины голосового сообщения
        voice_duration = update.message.voice.duration  # Длительность голосового сообщения в секундах
        print(f"===Trimming video to {voice_duration} seconds...")
        trim_video(video_path, trimmed_video_path, voice_duration)

        # Заменяем звуковую дорожку
        print("===Replacing audio in video...")
        replace_audio(trimmed_video_path, audio_path, video_with_audio_path)

        # Накладываем субтитры на видео
        print("===Adding subtitles to video...")

        # normalize_path for windows 
        subtitle_path = normalize_path(os.path.join(TEMP_DIR, f"subtitles_{update.message.chat_id}.srt"))
        video_with_audio_path = normalize_path(os.path.join(TEMP_DIR, f"video_audio_{update.message.chat_id}.mp4"))
        output_path = normalize_path(os.path.join(TEMP_DIR, f"output_{update.message.chat_id}.mp4"))
        subprocess.run([
            ffmpeg_cmd, '-i', video_with_audio_path, '-vf', f"subtitles={subtitle_path}:force_style='FontSize=24'",
            '-c:a', 'copy', output_path
        ], check=True)
        print("Video processing complete.")

        # Отправляем готовое видео пользователю
        print("Sending video to user...")
        with open(output_path, 'rb') as video:
            await update.message.reply_video(video=video, caption="Готово!")

    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"Ошибка обработки видео: {e}")
        print(f"Subprocess error: {e}")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {e}")
        print(f"General error: {e}")
    finally:
        # Удаляем временные файлы
        print("Cleaning up temporary files...")
        clean_temp_files(update.message.chat_id)
        print("Cleanup complete.")


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
    application = Application.builder().token(YOUR_BOT_TOKEN).connection_pool_size(20).connect_timeout(60).read_timeout(60).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    # Добавляем обработчик для всех остальных сообщений
    application.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND & ~filters.VOICE, 
        lambda update, context: handle_unauthorized_message(update, context)
    ))

    # Запускаем приложение
    application.run_polling()

async def handle_unauthorized_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработка всех остальных сообщений от неавторизованных пользователей.
    """
    user_id = update.effective_user.id
    
    if not is_user_authorized(user_id):
        await update.message.reply_text(
            "Извините, у вас нет доступа к этому боту. Он предназначен только для личного использования."
        )
        print(f"Unauthorized message from user ID: {user_id}")


if __name__ == "__main__":
    ffmpeg_cmd = find_ffmpeg_bin()
    main()
