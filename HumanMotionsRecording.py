import os
import cv2
import time
import datetime
import requests
import logging

# Thiết lập logger để ghi log
logging.basicConfig(filename='event_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# Directory to save images and videos
output_dir = r"C:\Users\khoil\Downloads\Coding"
os.makedirs(output_dir, exist_ok=True)

# Load Haar Cascade for face detection or upper body detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
upperbody_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    logging.error("Error: Cannot access the webcam!")
    exit()

# Initialize video_writer as None
video_writer = None
video_filename = ""
video_start_time = None
last_motion_time = None  # To track the last time motion or person was detected

# Background subtraction method for motion detection
fgbg = cv2.createBackgroundSubtractorMOG2()

# Telegram Bot configuration
BOT_TOKEN = "7171385980:AAHts1yco75v-q3mvha4H4n6QZrUmffPGV4"  # Replace with your Telegram Bot Token
CHAT_ID = "6229763712"      # Replace with your Chat ID

# Variables to limit notification noise
last_notification_time = time.time()
notification_interval = 1800  # Minimum time between notifications (in seconds)
event_counter = {"faces": 0, "upper_bodies": 0, "motions": 0}
last_summary_time = time.time()


# Function to log events
def log_event(message):
    logging.info(message)
    print(message)


# Function to send notifications via Telegram
def send_telegram_notification(message, urgent=False):
    global last_notification_time
    current_time = time.time()

    # Only send notification if it's urgent or the interval has passed
    if urgent or (current_time - last_notification_time >= notification_interval):
        last_notification_time = current_time
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message.encode('utf-8'), "parse_mode": "HTML"}
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                log_event("Telegram notification sent!")
            else:
                log_event(f"Failed to send notification: {response.text}")
        except Exception as e:
            log_event(f"Error sending Telegram notification: {e}")
    else:
        log_event("Notification skipped to avoid noise.")


# Function to send video to Telegram
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


# Function to start video recording
def start_video_capture():
    global video_writer, video_filename, video_start_time, last_motion_time
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    video_filename = os.path.join(output_dir, f'video_{timestamp}.avi')
    video_writer = cv2.VideoWriter(video_filename, cv2.VideoWriter_fourcc(*'XVID'), 20.0, (640, 480))
    video_start_time = datetime.datetime.now()
    last_motion_time = time.time()
    log_event(f"Started video recording: {video_filename}")
    send_telegram_notification("\U0001F3A5 Đang bắt đầu ghi hình vì phát hiện chuyển động của người!", urgent=True)


# Function to stop video recording and send video to Telegram
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
            caption=f"\U0001F6D1 Đã dừng ghi hình. Video dài {video_duration} giây, dung lượng {video_size / (1024 * 1024):.2f} MB"
        )


# Motion detection using contours
def detect_motion(frame):
    fgmask = fgbg.apply(frame)
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = False
    for contour in contours:
        if cv2.contourArea(contour) > 1000:  # Ngưỡng tối thiểu để nhận diện chuyển động
            motion_detected = True
            break
    return motion_detected


# Process each frame and detect motion and people
while True:
    # Read frame from webcam
    ret, frame = cap.read()
    if not ret:
        log_event("Error: Cannot read the frame!")
        break

    # Convert the current frame to grayscale and blur it
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # Detect face or upper body
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    upper_bodies = upperbody_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    person_detected = False

    # Motion detection
    motion_detected = detect_motion(frame)

    # Update counters for summary notifications
    event_counter["motions"] += 1 if motion_detected else 0
    event_counter["faces"] += len(faces)
    event_counter["upper_bodies"] += len(upper_bodies)

    # Check for faces or upper bodies
    for (x, y, w, h) in faces:
        person_detected = True
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Draw blue boxes for faces

    for (x, y, w, h) in upper_bodies:
        person_detected = True
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Draw blue boxes for upper body

    # Start video capture if motion and person detected
    if person_detected and motion_detected and video_writer is None:
        start_video_capture()

    # Write frame to video if recording
    if video_writer is not None:
        video_writer.write(frame)
        # Check if the video has been recording for more than 10 minutes (600 seconds)
        video_duration_seconds = (datetime.datetime.now() - video_start_time).seconds
        if video_duration_seconds >= 600:  # 10 minute
            stop_video_capture()

    # Stop video capture if no motion or person detected
    if video_writer is not None:
        if not person_detected or not motion_detected:
            if time.time() - last_motion_time > 5:
                stop_video_capture()

    # Update last_motion_time if motion or person detected
    if person_detected or motion_detected:
        last_motion_time = time.time()

    # Send summary notifications every 30 seconds
    if time.time() - last_summary_time > notification_interval:
        send_telegram_notification(
            f"Tóm tắt sự kiện: Khuôn mặt: {event_counter['faces']} lần, Người: {event_counter['upper_bodies']} lần, Chuyển động: {event_counter['motions']} lần"
        )
        event_counter = {"faces": 0, "upper_bodies": 0, "motions": 0}  # Reset counters
        last_summary_time = time.time()

    # Show the frame
    cv2.imshow('Webcam - Motion and Person Detection', frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()