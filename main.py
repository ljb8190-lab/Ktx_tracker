import os
import requests
from korail2 import Korail

# 1. 환경 변수에서 텔레그램 설정 가져오기
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# 2. 조회 설정
DEP_STATION = "포항"       # 출발역 (예: 서울, 용산, 대전, 동대구 등)
ARR_STATION = "천안아산"       # 도착역 (예: 부산, 광주송정, 여수엑스포 등)
TRAIN_DATE = "20260817"   # 탑승 날짜 (YYYYMMDD)

# 🕒 감시할 시간대 범위 설정 (시:분 24시간제)
START_TIME = "14:00"      # 조회 시작 시간 (예: 오전 8시부터)
END_TIME = "15:00"        # 조회 종료 시간 (예: 오후 2시까지)

def send_telegram_msg(message):
    """텔레그램 메시지 발송 함수"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
        print("텔레그램 알림 전송 성공")
    except Exception as e:
        print(f"텔레그램 알림 전송 실패: {e}")

def check_ktx_seats():
    try:
        korail = Korail2()
        
        # 코레일 API용 시작 시간 형식 변환 (HHMMSS)
        start_hhmmss = START_TIME.replace(":", "") + "00"
        
        # 열차 검색 (시작 시간 이후 열차들을 불러옴)
        trains = korail.search_train(
            dep=DEP_STATION,
            arr=ARR_STATION,
            date=TRAIN_DATE,
            time=start_hhmmss,
            passengers=None,
            include_no_seats=True
        )

        available_trains = []

        for train in trains:
            # 출발 시간 가공 (HH:MM)
            dep_time_str = f"{train.dep_time[:2]}:{train.dep_time[2:4]}"
            arr_time_str = f"{train.arr_time[:2]}:{train.arr_time[2:4]}"

            # 🕒 [핵심 추가] 설정한 종료 시간(END_TIME)을 넘어가는 열차는 필터링하여 제외
            if dep_time_str > END_TIME:
                continue

            # 일반실 및 특실 잔여 좌석 여부 확인
            has_general_seat = "예약가능" in str(train.general_seat_status)
            has_special_seat = "예약가능" in str(train.special_seat_status)

            if has_general_seat or has_special_seat:
                seat_type = []
                if has_general_seat: seat_type.append("일반실")
                if has_special_seat: seat_type.append("특실")

                available_trains.append({
                    "train_name": train.train_name,
                    "train_no": train.train_no,
                    "dep_time": dep_time_str,
                    "arr_time": arr_time_str,
                    "seats": ", ".join(seat_type)
                })

        return available_trains

    except Exception as e:
        print(f"코레일 조회 중 오류 발생: {e}")
        return []

def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("에러: TELEGRAM_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되어 있지 않습니다.")
        return

    print(f"[{DEP_STATION} ➔ {ARR_STATION} / {TRAIN_DATE} ({START_TIME}~{END_TIME})] KTX 취소표 감시 시작...")
    seats = check_ktx_seats()

    if seats:
        msg = f"🚅 *KTX 취소표(빈자리) 발견!*\n\n"
        msg += f"• *구간:* {DEP_STATION} ➔ {ARR_STATION}\n"
        msg += f"• *날짜:* {TRAIN_DATE[:4]}-{TRAIN_DATE[4:6]}-{TRAIN_DATE[6:]}\n"
        msg += f"• *시간대:* {START_TIME} ~ {END_TIME}\n"
        msg += f"───────────────\n\n"

        for train in seats:
            msg += f"• *[{train['train_name']} {train['train_no']}호]*\n"
            msg += f"  시간: {train['dep_time']} ➔ {train['arr_time']}\n"
            msg += f"  좌석: *{train['seats']} 가능*\n\n"

        msg += f"👉 *지금 코레일톡 앱에서 빠르게 예약하세요!*"
        send_telegram_msg(msg)
    else:
        print(f"지정한 시간대({START_TIME}~{END_TIME})에 예약 가능한 좌석이 없습니다.")

if __name__ == "__main__":
    main()
