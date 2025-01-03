import os
import cv2
import time
import datetime
import requests
import logging
import glob

logging.basicConfig(filename='event_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

output_dir = r"C:\Users\khoil\Downloads\Coding"
os.makedirs(output_dir, exist_ok=True)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
upperbody_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    logging.error("Error: Cannot access the webcam!")
    exit()

video_writer = None
video_filename = ""
video_start_time = None
last_motion_time = None

fgbg = cv2.createBackgroundSubtractorMOG2()

BOT_TOKEN = "7171385980:AAHts1yco75v-q3mvha4H4n6QZrUmffPGV4"
CHAT_ID = "6229763712"

last_notification_time = time.time()
notification_interval = 3600  # Minimum time between notifications (in seconds)
event_counter = {"faces": 0, "upper_bodies": 0, "motions": 0}
last_summary_time = time.time()

def log_event(message):
    logging.info(message)
    print(message)

def clean_old_videos(directory, days=7):
    """Delete videos older than the specified number of days"""
    cutoff_time = time.time() - days * 86400  # Convert days to seconds
    for file in glob.glob(os.path.join(directory, "*.mp4")):  # Change to .mp4
        if os.path.getmtime(file) < cutoff_time:
            os.remove(file)
            log_event(f"Deleted old video: {file}")

def send_telegram_notification(message, urgent=False):
    global last_notification_time
    current_time = time.time()

    if urgent or (current_time - last_notification_time >= notification_interval):
        last_notification_time = current_time
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                log_event("Telegram notification sent!")
            else:
                log_event(f"Failed to send notification: {response.text}")
        except Exception as e:
            log_event(f"Error sending Telegram notification: {e}")

def send_telegram_video(video_path, caption=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    files = {'video': open(video_path, 'rb')}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    try:
        response = requests.post(url, data=data, files=files)
        if response.status_code == 200:
            log_event(f"Telegram video sent successfully: {video_path}")
        else:
            log_event(f"Failed to send video: {response.text}")
    except Exception as e:
        log_event(f"Error sending video: {e}")
    finally:
        files['video'].close()

def start_video_capture():
    global video_writer, video_filename, video_start_time, last_motion_time
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    video_filename = os.path.join(output_dir, f'video_{timestamp}.mp4')  # Change extension to .mp4
    video_writer = cv2.VideoWriter(video_filename, cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (640, 480))  # Use 'mp4v'
    video_start_time = datetime.datetime.now()
    last_motion_time = time.time()
    log_event(f"Started video recording: {video_filename}")
    send_telegram_notification("\U0001F3A5 Motion detected! Starting video recording.", urgent=True)

def stop_video_capture():
    global video_writer, video_filename
    if video_writer is not None:
        video_writer.release()
        video_writer = None
        video_duration = (datetime.datetime.now() - video_start_time).seconds
        video_size = os.path.getsize(video_filename)
        log_event(f"Stopped video recording: {video_filename}")
        log_event(f"Video duration: {video_duration} seconds, Size: {video_size / (1024 * 1024):.2f} MB")
        send_telegram_video(
            video_filename,
            caption=f"\U0001F6D1 Recording stopped. Duration: {video_duration} seconds, Size: {video_size / (1024 * 1024):.2f} MB"
        )

def detect_motion(frame):
    fgmask = fgbg.apply(frame)
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = False
    for contour in contours:
        if cv2.contourArea(contour) > 1000:  # Minimum threshold for detecting motion
            motion_detected = True
            break
    return motion_detected

while True:
    ret, frame = cap.read()
    if not ret:
        log_event("Error: Cannot read the frame!")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    upper_bodies = upperbody_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    motion_detected = detect_motion(frame)

    event_counter["motions"] += 1 if motion_detected else 0
    event_counter["faces"] += len(faces)
    event_counter["upper_bodies"] += len(upper_bodies)

    people_count = len(faces) + len(upper_bodies)

    cv2.putText(frame, f"People: {people_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Face

    for (x, y, w, h) in upper_bodies:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Upper body

    if len(faces) > 0 or motion_detected:
        if video_writer is None:
            start_video_capture()

    if video_writer is not None:
        video_writer.write(frame)
        if (datetime.datetime.now() - video_start_time).seconds >= 600:
            stop_video_capture()

    if video_writer is not None and not (len(faces) > 0 or motion_detected):
        if time.time() - last_motion_time > 5:
            stop_video_capture()

    clean_old_videos(output_dir, days=1)

    if time.time() - last_summary_time > notification_interval:
        send_telegram_notification(
            f"Summary: Faces detected: {event_counter['faces']}, Upper bodies detected: {event_counter['upper_bodies']}, Motions detected: {event_counter['motions']}"
        )
        event_counter = {"faces": 0, "upper_bodies": 0, "motions": 0}
        last_summary_time = time.time()

    cv2.imshow('Webcam - Motion and Person Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()