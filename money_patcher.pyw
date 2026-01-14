import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
import os
import json
import sys
import webbrowser
import time
import cv2
import numpy as np
import mss
import pyautogui
import subprocess
import threading

def search_and_click_image(image_filename, threshold=0.8):
    """
    화면에서 이미지를 찾아 클릭합니다.
    
    Args:
        image_filename: 찾을 이미지 파일명
        threshold: 매칭 임계값 (0.0~1.0)
    
    Returns:
        bool: 이미지를 찾아 클릭했으면 True, 못 찾았으면 False
    """
    try:
        # 이미지 파일 경로 확인
        if not os.path.exists(image_filename):
            print(f"이미지 파일을 찾을 수 없습니다: {image_filename}")
            return False
        
        # 템플릿 이미지 로드
        template = cv2.imread(image_filename)
        if template is None:
            print(f"이미지 로드 실패: {image_filename}")
            return False
        
        template_height, template_width = template.shape[:2]
        
        # 화면 캡처 (1920x1080 범위로 제한)
        with mss.mss() as sct:
            monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}
            screenshot = sct.grab(monitor)
            
            # numpy 배열로 변환
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # 템플릿 매칭
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 임계값 이상이면 클릭
        if max_val >= threshold:
            # 중앙 좌표 계산
            center_x = max_loc[0] + template_width // 2
            center_y = max_loc[1] + template_height // 2
            
            # 클릭 (마우스 다운 -> 업)
            pyautogui.moveTo(center_x, center_y)
            pyautogui.mouseDown()
            time.sleep(0.05)
            pyautogui.mouseUp()
            print(f"이미지 발견 및 클릭: ({center_x}, {center_y}), 신뢰도: {max_val:.2f}")
            return True
        else:
            print(f"이미지를 찾지 못했습니다. 최대 신뢰도: {max_val:.2f}")
            return False
    
    except Exception as e:
        print(f"이미지 검색 중 오류 발생: {e}")
        return False

def search_image_only(image_filename, threshold=0.5):
    """
    화면에서 이미지를 찾기만 합니다 (클릭하지 않음).
    
    Args:
        image_filename: 찾을 이미지 파일명
        threshold: 매칭 임계값 (0.0~1.0)
    
    Returns:
        bool: 이미지를 찾았으면 True, 못 찾았으면 False
    """
    try:
        # 이미지 파일 경로 확인
        if not os.path.exists(image_filename):
            print(f"이미지 파일을 찾을 수 없습니다: {image_filename}")
            return False
        
        # 템플릿 이미지 로드
        template = cv2.imread(image_filename)
        if template is None:
            print(f"이미지 로드 실패: {image_filename}")
            return False
        
        # 화면 캡처 (1920x1080 범위로 제한)
        with mss.mss() as sct:
            monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}
            screenshot = sct.grab(monitor)
            
            # numpy 배열로 변환
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # 템플릿 매칭
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 임계값 이상이면 발견
        if max_val >= threshold:
            print(f"{image_filename} 발견: 신뢰도 {max_val:.2f}")
            return True
        else:
            print(f"{image_filename} 미발견: 최대 신뢰도 {max_val:.2f}")
            return False
    
    except Exception as e:
        print(f"이미지 검색 중 오류 발생: {e}")
        return False

class MoneyPatcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("귀혼 패치기")
        self.root.geometry("160x160")
        self.root.resizable(False, False)
        
        # 캡션 제거
        self.root.overrideredirect(True)
        
        # 항상 최상단에 유지
        self.root.attributes('-topmost', True)
        
        # 화면 오른쪽 끝에 위치
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - 200 - 60  # 오른쪽 끝에서 60px 왼쪽
        y = 50  # 상단에서 50px 아래
        self.root.geometry(f"200x410+{x}+{y}")  # 모니터링 시간 버튼 추가
        
        # 드래그 이동을 위한 변수
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # 마우스 드래그 이벤트 바인딩
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.on_drag)
        
        # 중앙 정렬을 위한 메인 프레임
        main_frame = tk.Frame(self.root)
        main_frame.pack(side='bottom', fill='both', padx=8, pady=(8, 8))
        
        # 메인 프레임에도 드래그 이벤트 바인딩
        main_frame.bind('<Button-1>', self.start_drag)
        main_frame.bind('<B1-Motion>', self.on_drag)
        
        # 모니터링 버튼 프레임 (맨 위)
        monitor_frame = tk.Frame(main_frame)
        monitor_frame.pack(pady=3)
        
        # 모니터링 시작 버튼
        self.monitor_start_btn = tk.Button(
            monitor_frame,
            text="모니터링 시작",
            font=("Arial", 7, "bold"),
            width=10,
            height=1,
            bg="#2196F3",
            fg="white",
            command=self.start_monitoring
        )
        self.monitor_start_btn.pack(side='left', padx=2)
        
        # 모니터링 정지 버튼
        self.monitor_stop_btn = tk.Button(
            monitor_frame,
            text="모니터링 정지",
            font=("Arial", 7, "bold"),
            width=10,
            height=1,
            bg="#FF5722",
            fg="white",
            command=self.stop_monitoring
        )
        self.monitor_stop_btn.pack(side='left', padx=2)
        
        # 모니터링 상태 표시 레이블
        monitor_status_frame = tk.Frame(main_frame)
        monitor_status_frame.pack(pady=2)
        
        self.monitor_status_label = tk.Label(
            monitor_status_frame,
            text="상태: 정지 중",
            font=("Arial", 7, "bold"),
            fg="#FF5722"
        )
        self.monitor_status_label.pack()
        
        # 모니터링 시간 선택 프레임
        time_frame = tk.Frame(main_frame)
        time_frame.pack(pady=3)
        
        # 모니터링 시간 레이블
        time_label = tk.Label(time_frame, text="모니터링 간격:", font=("Arial", 6))
        time_label.pack(pady=2)
        
        # 시간 버튼 프레임
        time_btn_frame = tk.Frame(time_frame)
        time_btn_frame.pack()
        
        # 10분 버튼
        self.time_30_btn = tk.Button(
            time_btn_frame,
            text="10분",
            font=("Arial", 7),
            width=5,
            height=1,
            bg="#2196F3",
            fg="white",
            command=lambda: self.set_monitor_time(10)
        )
        self.time_30_btn.pack(side='left', padx=1)
        
        # 20분 버튼
        self.time_60_btn = tk.Button(
            time_btn_frame,
            text="20분",
            font=("Arial", 7),
            width=5,
            height=1,
            bg="#2196F3",
            fg="white",
            command=lambda: self.set_monitor_time(20)
        )
        self.time_60_btn.pack(side='left', padx=1)
        
        # 30분 버튼
        self.time_90_btn = tk.Button(
            time_btn_frame,
            text="30분",
            font=("Arial", 7),
            width=5,
            height=1,
            bg="#4CAF50",
            fg="white",
            command=lambda: self.set_monitor_time(30)
        )
        self.time_90_btn.pack(side='left', padx=1)
        
        # 체크박스 프레임
        checkbox_frame = tk.Frame(main_frame)
        checkbox_frame.pack(pady=3)
        
        # 한게임 체크박스
        self.hangame_var = tk.BooleanVar(value=True)
        self.hangame_checkbox = tk.Checkbutton(
            checkbox_frame,
            text="한게임",
            font=("Arial", 7),
            variable=self.hangame_var,
            command=self.toggle_hangame
        )
        self.hangame_checkbox.pack(side='left', padx=6)
        
        # 엠게임 체크박스
        self.mgame_var = tk.BooleanVar(value=False)
        self.mgame_checkbox = tk.Checkbutton(
            checkbox_frame,
            text="엠게임",
            font=("Arial", 7),
            variable=self.mgame_var,
            command=self.toggle_mgame
        )
        self.mgame_checkbox.pack(side='left', padx=6)
        
        # 텍스트 입력 프레임
        input_frame = tk.Frame(main_frame)
        input_frame.pack(pady=3)
        
        # ID 라벨과 입력
        id_label = tk.Label(input_frame, text="ID:", font=("Arial", 7))
        id_label.grid(row=0, column=0, sticky='w', pady=3)
        
        self.id_entry = tk.Entry(input_frame, font=("Arial", 7), width=16, state='readonly')
        self.id_entry.grid(row=0, column=1, padx=3, pady=3)
        self.id_entry.bind('<Double-Button-1>', self.select_all_id)
        self.id_entry.bind('<FocusOut>', self.lock_id_entry)
        
        # PW 라벨과 입력
        pw_label = tk.Label(input_frame, text="PW:", font=("Arial", 7))
        pw_label.grid(row=1, column=0, sticky='w', pady=3)
        
        self.pw_entry = tk.Entry(input_frame, font=("Arial", 7), width=16, show="*", state='readonly')
        self.pw_entry.grid(row=1, column=1, padx=3, pady=3)
        self.pw_entry.bind('<Double-Button-1>', self.select_all_pw)
        self.pw_entry.bind('<FocusOut>', self.lock_pw_entry)
        
        # 이미지 버튼 프레임
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=6)
        
        # 버튼 상태 추적
        self.is_started = False
        self.is_stopped = False
        self.is_exited = False
        self.stop_flag = False  # 작업 중지 플래그
        self.monitor_thread = None  # 30분 모니터링 스레드
        self.monitor_running = False  # 모니터링 실행 상태
        self.monitor_interval = 1800  # 모니터링 간격 (기본 30분 = 1800초)
        
        # 시작 버튼
        self.start_btn = tk.Button(
            button_frame,
            text="시작",
            font=("Arial", 8, "bold"),
            width=5,
            height=1,
            bg="#4CAF50",
            fg="white",
            command=self.toggle_start
        )
        self.start_btn.pack(side='left', padx=1)
        
        # 정지 버튼
        self.stop_btn = tk.Button(
            button_frame,
            text="정지",
            font=("Arial", 8, "bold"),
            width=5,
            height=1,
            bg="#FF9800",
            fg="white",
            command=self.toggle_stop
        )
        self.stop_btn.pack(side='left', padx=1)
        
        # 종료 버튼
        self.exit_btn = tk.Button(
            button_frame,
            text="종료",
            font=("Arial", 8, "bold"),
            width=5,
            height=1,
            bg="#F44336",
            fg="white",
            command=self.toggle_exit
        )
        self.exit_btn.pack(side='left', padx=1)
        
        # 채널 선택 프레임
        channel_frame = tk.Frame(main_frame)
        channel_frame.pack(pady=3)
        
        # 채널 체크박스 변수 초기화
        self.channel_vars = []
        for i in range(8):
            var = tk.BooleanVar(value=False)
            self.channel_vars.append(var)
        
        # 1~4채널 (첫 번째 줄)
        channel_row1 = tk.Frame(channel_frame)
        channel_row1.pack()
        for i in range(4):
            cb = tk.Checkbutton(
                channel_row1,
                text=f"{i+1}ch",
                font=("Arial", 6),
                variable=self.channel_vars[i]
            )
            cb.pack(side='left', padx=2)
        
        # 5~8채널 (두 번째 줄)
        channel_row2 = tk.Frame(channel_frame)
        channel_row2.pack()
        for i in range(4, 8):
            cb = tk.Checkbutton(
                channel_row2,
                text=f"{i+1}ch",
                font=("Arial", 6),
                variable=self.channel_vars[i]
            )
            cb.pack(side='left', padx=2)
        
        # 상태 표시 레이블
        self.status_label = tk.Label(main_frame, text="", font=("Arial", 6))
        self.status_label.pack(pady=3)
        
        # 로그 출력 영역 (하단)
        log_frame = tk.Frame(main_frame)
        log_frame.pack(pady=3, fill='both', expand=True)
        
        # 스크롤 가능한 텍스트 위젯
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 14),
            height=5,
            width=20,
            wrap=tk.WORD,
            bg="#1e1e1e",
            fg="#00ff00"
        )
        self.log_text.pack(fill='both', expand=True)
        
        # 저장된 ID/PW 불러오기
        self.load_credentials()
        
        # 초기 로그 메시지
        self.log("프로그램 초기화 완료")
    
    def log(self, message):
        """GUI 로그 영역에 메시지 출력"""
        try:
            timestamp = time.strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {message}\n"
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)  # 자동 스크롤
            print(message)  # 콘솔에도 출력
        except Exception as e:
            print(f"로그 출력 오류: {e}")
    
    def load_credentials(self):
        """저장된 ID/PW와 체크박스 상태를 불러옵니다."""
        try:
            if os.path.exists('credentials.json'):
                with open('credentials.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # readonly 상태에서 삽입하기 위해 임시로 normal 상태로 변경
                    self.id_entry.config(state='normal')
                    self.pw_entry.config(state='normal')
                    
                    self.id_entry.insert(0, data.get('id', ''))
                    self.pw_entry.insert(0, data.get('pw', ''))
                    
                    # 다시 readonly 상태로 변경
                    self.id_entry.config(state='readonly')
                    self.pw_entry.config(state='readonly')
                    
                    # 한게임/엠게임 체크박스 상태 복원
                    self.hangame_var.set(data.get('hangame', True))
                    self.mgame_var.set(data.get('mgame', False))
                    
                    # 채널 체크박스 상태 복원
                    channels = data.get('channels', [False] * 8)
                    for i in range(8):
                        if i < len(channels):
                            self.channel_vars[i].set(channels[i])
                    
                    print("저장된 계정 정보 및 설정 로드 완료")
        except Exception as e:
            print(f"계정 정보 로드 실패: {e}")
    
    def save_credentials(self):
        """현재 ID/PW와 체크박스 상태를 저장합니다."""
        try:
            # 채널 체크박스 상태 수집
            channels = [self.channel_vars[i].get() for i in range(8)]
            
            data = {
                'id': self.id_entry.get(),
                'pw': self.pw_entry.get(),
                'hangame': self.hangame_var.get(),
                'mgame': self.mgame_var.get(),
                'channels': channels
            }
            with open('credentials.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("계정 정보 및 설정 저장 완료")
        except Exception as e:
            print(f"계정 정보 저장 실패: {e}")
    
    def toggle_start(self):
        """시작 버튼 토글"""
        if not self.is_started:
            self.is_started = True
            self.is_stopped = False
            self.is_exited = False
            self.stop_flag = False  # 플래그 초기화
            self.start_btn.config(bg="#388E3C")
            self.stop_btn.config(bg="#FF9800")
            self.exit_btn.config(bg="#F44336")
            self.status_label.config(text="시작됨")
            self.log("프로그램 시작")
            
            # 체크박스에 따라 브라우저 접속 (스레드로 실행)
            if self.hangame_var.get():
                thread = threading.Thread(target=self.start_hangame)
                thread.daemon = True
                thread.start()
            elif self.mgame_var.get():
                thread = threading.Thread(target=self.start_mgame)
                thread.daemon = True
                thread.start()
        else:
            self.is_started = False
            self.start_btn.config(bg="#4CAF50")
            self.status_label.config(text="")
    
    def toggle_stop(self):
        """정지 버튼 토글"""
        if not self.is_stopped:
            self.is_started = False
            self.is_stopped = True
            self.is_exited = False
            self.stop_flag = True  # 작업 중지 플래그 설정
            self.start_btn.config(bg="#4CAF50")
            self.stop_btn.config(bg="#E65100")
            self.exit_btn.config(bg="#F44336")
            self.status_label.config(text="정지됨")
            self.log("프로그램 정지")
        else:
            self.is_stopped = False
            self.stop_btn.config(bg="#FF9800")
            self.status_label.config(text="")
    
    def toggle_exit(self):
        """종료 버튼 토글"""
        if not self.is_exited:
            self.is_started = False
            self.is_stopped = False
            self.is_exited = True
            self.start_btn.config(bg="#4CAF50")
            self.stop_btn.config(bg="#FF9800")
            self.exit_btn.config(bg="#C62828")
            self.status_label.config(text="종료됨")
            self.log("프로그램 종료")
            # ID/PW 저장
            self.save_credentials()
            # 프로그램 종료
            self.root.quit()
            self.root.destroy()
        else:
            self.is_exited = False
            self.exit_btn.config(bg="#F44336")
            self.status_label.config(text="")
    
    def start_drag(self, event):
        """마우스 드래그 시작"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def on_drag(self, event):
        """마우스 드래그 중 창 이동"""
        x = self.root.winfo_x() + event.x - self.drag_start_x
        y = self.root.winfo_y() + event.y - self.drag_start_y
        self.root.geometry(f"+{x}+{y}")
    
    def select_all_id(self, event):
        """ID 입력 필드 더블클릭 시 편집 가능 상태로 변경 및 전체 선택"""
        self.id_entry.config(state='normal')
        self.id_entry.select_range(0, tk.END)
        self.id_entry.icursor(tk.END)
        return 'break'
    
    def select_all_pw(self, event):
        """PW 입력 필드 더블클릭 시 편집 가능 상태로 변경 및 전체 선택"""
        self.pw_entry.config(state='normal')
        self.pw_entry.select_range(0, tk.END)
        self.pw_entry.icursor(tk.END)
        return 'break'
    
    def lock_id_entry(self, event):
        """ID 입력 필드 포커스 아웃 시 readonly 상태로 변경"""
        self.id_entry.config(state='readonly')
    
    def lock_pw_entry(self, event):
        """PW 입력 필드 포커스 아웃 시 readonly 상태로 변경"""
        self.pw_entry.config(state='readonly')
    
    def toggle_hangame(self):
        """한게임 체크박스 토글"""
        if self.hangame_var.get():
            self.mgame_var.set(False)
            self.log("한게임 선택")
    
    def toggle_mgame(self):
        """엠게임 체크박스 토글"""
        if self.mgame_var.get():
            self.hangame_var.set(False)
            self.log("엠게임 선택")
    
    def start_hangame(self):
        """한게임 접속 프로세스"""
        try:
            self.log("한게임 접속 시작")
            self.status_label.config(text="한게임 접속 중...")
            
            # hellper 이미지 체크 (유사도 50% 이상)
            self.log("hellper 이미지 서치 중...")
            hellper_found = search_image_only('hellper.png', threshold=0.5)
            
            if not hellper_found:
                self.log("hellper 미발견 - start.bat 실행")
                self.run_local_start_bat()
                # 배치파일 실행 후 대기
                time.sleep(10)
                
                # hellper 재시도 (최대 3회, 10초 간격)
                max_attempts = 3
                for attempt in range(1, max_attempts + 1):
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    
                    self.log(f"hellper 검색 재시도 {attempt}/{max_attempts}회")
                    hellper_found = search_image_only('hellper.png', threshold=0.5)
                    
                    if hellper_found:
                        self.log(f"hellper 발견 ({attempt}회 시도)")
                        break
                    
                    if attempt < max_attempts:
                        self.log(f"hellper 미발견, 10초 후 재시도...")
                        time.sleep(10)
                
                # 3회 시도 후에도 미발견 시 중단
                if not hellper_found:
                    self.log(f"hellper {max_attempts}회 시도 실패 - 매크로 시작 안함")
                    return
            else:
                self.log("hellper 발견 - 진행")
            
            # 크롬 브라우저를 최대화 상태로 열기
            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            subprocess.Popen([chrome_path, '--start-maximized', 'https://hon.hangame.com/'])
            
            # 5초 대기 (페이지 로딩)
            time.sleep(5)
            if self.stop_flag:
                self.log("작업 중지됨")
                return
            
            # 동일한 주소를 다른 탭으로 열기
            self.log("새 탭에서 한게임 열기")
            pyautogui.hotkey('ctrl', 't')
            time.sleep(1)
            pyautogui.write('hon.hangame.com', interval=0.05)
            pyautogui.press('enter')
            time.sleep(3)
            if self.stop_flag:
                self.log("작업 중지됨")
                return
            
            # 로그인 페이지 버튼 좌표 클릭
            pyautogui.click(640, 690)
            self.log("로그인 페이지 버튼 클릭 (640, 690)")
            
            # 페이지 로딩 대기
            time.sleep(5)
            if self.stop_flag:
                self.log("작업 중지됨")
                return
            
            # 한게임 로그인 버튼 좌표 클릭 (x=1065, y=239)
            pyautogui.moveTo(1065, 239)
            pyautogui.mouseDown()
            time.sleep(0.05)
            pyautogui.mouseUp()
            self.log("로그인 버튼 클릭 (1065, 239)")
            time.sleep(0.5)
            if self.stop_flag:
                self.log("작업 중지됨")
                return
            
            # ID 입력
            user_id = self.id_entry.get()
            self.log(f"ID 입력 시작: {user_id}")
            if user_id:
                pyautogui.write(user_id, interval=0.05)
                self.log("ID 입력 완료")
                
                # 1초 대기
                time.sleep(1)
                if self.stop_flag:
                    self.log("작업 중지됨")
                    return
                
                # TAB 키로 다음 필드 이동
                pyautogui.press('tab')
                self.log("TAB 키 입력 완료")
                
                # 1초 대기
                time.sleep(1)
                if self.stop_flag:
                    self.log("작업 중지됨")
                    return
                
                # PW 입력
                user_pw = self.pw_entry.get()
                self.log("PW 입력 시작")
                if user_pw:
                    pyautogui.write(user_pw, interval=0.05)
                    self.log("PW 입력 완료")
                    
                    # 엔터 키 입력
                    pyautogui.press('enter')
                    self.log("로그인 엔터키 입력")
                    
                    # 로그인 후 대기
                    time.sleep(8)
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    
                    # 한게임 시작 버튼 좌표 클릭
                    self.log("한게임 시작 버튼 클릭 시작")
                    pyautogui.click(600, 450)
                    self.log("한게임 시작 버튼 클릭 (600, 450)")
                    
                    # 추가 클릭
                    time.sleep(8)
                    pyautogui.click(1234, 772)
                    self.log("추가 클릭 (1234, 772)")
                    
                    # 35초 대기
                    self.log("35초 대기 시작")
                    time.sleep(35)
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    
                    # neco.png 이미지 서칭 (5초 간격, 최대 5회 시도)
                    self.log("neco.png 서칭 시작 (최대 5회)")
                    found = False
                    max_attempts = 5
                    for attempt in range(1, max_attempts + 1):
                        if self.stop_flag:
                            self.log("작업 중지됨")
                            return
                        
                        print(f"neco.png 검색 시도 {attempt}/{max_attempts}회")
                        
                        # 이미지 서칭 (유사도 50%)
                        if search_and_click_image('neco.png', threshold=0.5):
                            print("neco.png 발견, 더블클릭 실행")
                            time.sleep(0.2)
                            # 더블클릭
                            pyautogui.doubleClick()
                            print("더블클릭 완료")
                            found = True
                            break
                        
                        # 마지막 시도가 아니면 5초 대기
                        if attempt < max_attempts:
                            time.sleep(5)
                    
                    # 5회 시도 후 실패시 좌표 더블클릭
                    if not found:
                        print("neco.png 서칭 실패, 좌표 더블클릭 (970, 437)")
                        pyautogui.doubleClick(970, 437)
                        print("좌표 더블클릭 완료")
                    
                    # 5초 대기 후 크롬 브라우저 활성화 및 로그아웃 처리
                    time.sleep(5)
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    
                    print("크롬 브라우저 활성화")
                    # 크롬 브라우저 영역 클릭하여 활성화
                    pyautogui.click(1700, 800)  # 화면 우하단 클릭
                    time.sleep(1)
                    
                    # logout 이미지 서칭 및 클릭
                    print("logout 이미지 서칭")
                    if search_and_click_image('logout.png', threshold=0.5):
                        print("logout 이미지 클릭 완료")
                        time.sleep(2)
                    else:
                        print("logout 이미지 미발견")
                    
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    
                    print("크롬 브라우저 닫기")
                    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
                    time.sleep(1)
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    
                    # 체크된 채널 좌표 더블클릭
                    time.sleep(1)
                    for i in range(8):
                        if self.channel_vars[i].get():
                            channel_y = 450 + (i * 30)
                            print(f"{i+1}채널 더블클릭 (1000, {channel_y})")
                            pyautogui.doubleClick(1000, channel_y)
                            time.sleep(0.5)
                            if self.stop_flag:
                                self.log("작업 중지됨")
                                return
                    
                    # 5초 대기 후 추가 클릭
                    time.sleep(5)
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    print("추가 클릭 (1380, 860)")
                    pyautogui.moveTo(1380, 860)
                    time.sleep(0.05)
                    pyautogui.mouseDown()
                    time.sleep(0.05)
                    pyautogui.mouseUp()
                    
                    # 15초 대기 후 autokeyboard 이미지 확인
                    time.sleep(15)
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    print("autokeyboard.png 이미지 서칭")
                    if not search_image_only('autokeyboard.png', threshold=0.5):
                        print("autokeyboard 미발견 - F2 키 입력")
                        pyautogui.press('f2')
                        print("F2 키 입력 완료")
                    else:
                        print("autokeyboard 발견 - F2 키 입력 스킵")
            
            self.status_label.config(text="한게임 로그인 페이지 열림")
            self.log("한게임 접속 완료 - 모니터링은 수동으로 시작하세요")
        
        except Exception as e:
            print(f"한게임 접속 중 오류: {e}")
            self.status_label.config(text="오류 발생")
    
    def start_mgame(self):
        """엠게임 접속 프로세스"""
        try:
            self.log("엠게임 접속 시작")
            self.status_label.config(text="엠게임 접속 중...")
            
            # hellper 이미지 체크 (유사도 50% 이상)
            self.log("hellper 이미지 서치 중...")
            hellper_found = search_image_only('hellper.png', threshold=0.5)
            
            if not hellper_found:
                self.log("hellper 미발견 - start.bat 실행")
                self.run_local_start_bat()
                # 배치파일 실행 후 대기
                time.sleep(10)
                
                # hellper 재시도 (최대 3회, 10초 간격)
                max_attempts = 3
                for attempt in range(1, max_attempts + 1):
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    
                    self.log(f"hellper 검색 재시도 {attempt}/{max_attempts}회")
                    hellper_found = search_image_only('hellper.png', threshold=0.5)
                    
                    if hellper_found:
                        self.log(f"hellper 발견 ({attempt}회 시도)")
                        break
                    
                    if attempt < max_attempts:
                        self.log(f"hellper 미발견, 10초 후 재시도...")
                        time.sleep(10)
                
                # 3회 시도 후에도 미발견 시 중단
                if not hellper_found:
                    self.log(f"hellper {max_attempts}회 시도 실패 - 매크로 시작 안함")
                    return
            else:
                self.log("hellper 발견 - 진행")
            
            # 크롬 브라우저를 최대화 상태로 열기
            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            subprocess.Popen([chrome_path, '--start-maximized', 'https://hon.mgame.com/'])
            
            # 5초 대기 (페이지 로딩)
            time.sleep(5)
            if self.stop_flag:
                self.log("작업 중지됨")
                return
            
            # 동일한 주소를 다른 탭으로 열기
            print("새 탭에서 엠게임 열기")
            pyautogui.hotkey('ctrl', 't')
            time.sleep(1)
            pyautogui.write('hon.mgame.com', interval=0.05)
            pyautogui.press('enter')
            time.sleep(3)
            if self.stop_flag:
                self.log("작업 중지됨")
                return
            
            # 로그인 페이지 버튼 좌표 클릭
            pyautogui.click(600, 660)
            self.log("로그인 페이지 버튼 클릭 (600, 660)")
            
            # 페이지 로딩 대기
            time.sleep(5)
            if self.stop_flag:
                self.log("작업 중지됨")
                return
            
            # 엠게임 로그인 버튼 좌표 클릭 (x=775, y=267)
            pyautogui.moveTo(775, 267)
            pyautogui.mouseDown()
            time.sleep(0.05)
            pyautogui.mouseUp()
            self.log("로그인 버튼 클릭 (775, 267)")
            time.sleep(0.5)
            if self.stop_flag:
                self.log("작업 중지됨")
                return
            
            # ID 입력
            user_id = self.id_entry.get()
            self.log(f"ID 입력 시작: {user_id}")
            if user_id:
                pyautogui.write(user_id, interval=0.05)
                self.log("ID 입력 완료")
                
                # 1초 대기
                time.sleep(1)
                if self.stop_flag:
                    self.log("작업 중지됨")
                    return
                
                # TAB 키로 다음 필드 이동
                pyautogui.press('tab')
                self.log("TAB 키 입력 완료")
                
                # 1초 대기
                time.sleep(1)
                if self.stop_flag:
                    self.log("작업 중지됨")
                    return
                
                # PW 입력
                user_pw = self.pw_entry.get()
                self.log("PW 입력 시작")
                if user_pw:
                    pyautogui.write(user_pw, interval=0.05)
                    self.log("PW 입력 완료")
                    
                    # 엔터 키 입력
                    pyautogui.press('enter')
                    self.log("로그인 엔터키 입력")
                    
                   # 로그인 후 대기
                    time.sleep(8)
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    
                    # 엠게임 시작 버튼 좌표 클릭
                    self.log("엠게임 시작 버튼 클릭 시작")
                    pyautogui.click(600, 450)
                    self.log("엠게임 시작 버튼 클릭 (600, 450)")
                    
                    # 추가 클릭
                    time.sleep(8)
                    pyautogui.click(1234, 772)
                    self.log("추가 클릭 (1234, 772)")
                    
                    # 35초 대기
                    self.log("35초 대기 시작")
                    time.sleep(35)
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    
                    # neco.png 이미지 서칭 (5초 간격, 최대 5회 시도)
                    self.log("neco.png 서칭 시작 (최대 5회)")
                    found = False
                    max_attempts = 5
                    for attempt in range(1, max_attempts + 1):
                        if self.stop_flag:
                            self.log("작업 중지됨")
                            return
                        
                        print(f"neco.png 검색 시도 {attempt}/{max_attempts}회")
                        
                        # 이미지 서칭 (유사도 50%)
                        if search_and_click_image('neco.png', threshold=0.5):
                            print("neco.png 발견, 더블클릭 실행")
                            time.sleep(0.2)
                            # 더블클릭
                            pyautogui.doubleClick()
                            print("더블클릭 완료")
                            found = True
                            break
                        
                        # 마지막 시도가 아니면 5초 대기
                        if attempt < max_attempts:
                            time.sleep(5)
                    
                    # 5회 시도 후 실패시 좌표 더블클릭
                    if not found:
                        print("neco.png 서칭 실패, 좌표 더블클릭 (970, 437)")
                        pyautogui.doubleClick(970, 437)
                        print("좌표 더블클릭 완료")
                    
                    # 5초 대기 후 크롬 브라우저 활성화 및 로그아웃 처리
                    time.sleep(5)
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    
                    print("크롬 브라우저 활성화")
                    # 크롬 브라우저 영역 클릭하여 활성화
                    pyautogui.click(1700, 800)  # 화면 우하단 클릭
                    time.sleep(1)
                    
                    # logout 이미지 서칭 및 클릭
                    print("logout 이미지 서칭")
                    if search_and_click_image('logout.png', threshold=0.5):
                        print("logout 이미지 클릭 완료")
                        time.sleep(2)
                    else:
                        print("logout 이미지 미발견")
                    
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    
                    print("크롬 브라우저 닫기")
                    subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
                    time.sleep(1)
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    
                    # 체크된 채널 좌표 더블클릭
                    time.sleep(1)
                    for i in range(8):
                        if self.channel_vars[i].get():
                            channel_y = 450 + (i * 30)
                            print(f"{i+1}채널 더블클릭 (1000, {channel_y})")
                            pyautogui.doubleClick(1000, channel_y)
                            time.sleep(0.5)
                            if self.stop_flag:
                                self.log("작업 중지됨")
                                return
                    
                    # 5초 대기 후 추가 클릭
                    time.sleep(5)
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    print("추가 클릭 (1380, 860)")
                    pyautogui.moveTo(1380, 860)
                    time.sleep(0.05)
                    pyautogui.mouseDown()
                    time.sleep(0.05)
                    pyautogui.mouseUp()
                    
                    # 5초 대기 후 autokeyboard 이미지 확인
                    time.sleep(5)
                    if self.stop_flag:
                        self.log("작업 중지됨")
                        return
                    print("autokeyboard.png 이미지 서칭")
                    if not search_image_only('autokeyboard.png', threshold=0.5):
                        print("autokeyboard 미발견 - F2 키 입력")
                        pyautogui.press('f2')
                        print("F2 키 입력 완료")
                    else:
                        print("autokeyboard 발견 - F2 키 입력 스킵")
            
            self.status_label.config(text="엠게임 로그인 페이지 열림")
            self.log("엠게임 접속 완료 - 모니터링은 수동으로 시작하세요")
        
        except Exception as e:
            print(f"엠게임 접속 중 오류: {e}")
            self.status_label.config(text="오류 발생")
    
    def set_monitor_time(self, minutes):
        """모니터링 시간 설정"""
        self.monitor_interval = minutes * 60  # 분을 초로 변환
        
        # 모든 버튼 색상 초기화
        self.time_30_btn.config(bg="#2196F3")
        self.time_60_btn.config(bg="#2196F3")
        self.time_90_btn.config(bg="#2196F3")
        
        # 선택된 버튼 강조
        if minutes == 10:
            self.time_30_btn.config(bg="#4CAF50")
        elif minutes == 20:
            self.time_60_btn.config(bg="#4CAF50")
        elif minutes == 30:
            self.time_90_btn.config(bg="#4CAF50")
        
        self.log(f"모니터링 간격: {minutes}분으로 설정")
    
    def start_monitoring(self):
        """모니터링 수동 시작"""
        if not self.monitor_running:
            self.monitor_running = True
            self.monitor_thread = threading.Thread(target=self.monitor_30min_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            self.monitor_start_btn.config(bg="#1976D2")
            self.monitor_status_label.config(text="상태: 모니터링 중", fg="#4CAF50")
            self.log("모니터링 시작")
    
    def stop_monitoring(self):
        """모니터링 수동 정지"""
        self.monitor_running = False
        self.monitor_start_btn.config(bg="#2196F3")
        self.monitor_status_label.config(text="상태: 정지 중", fg="#FF5722")
        self.log("모니터링 정지")
    
    def start_30min_monitor(self):
        """모니터링 자동 시작 (선택된 시간 간격 사용)"""
        if not self.monitor_running:
            self.monitor_running = True
            self.monitor_thread = threading.Thread(target=self.monitor_30min_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            minutes = self.monitor_interval // 60
            self.log(f"{minutes}분 단위 모니터링 자동 시작")
    
    def monitor_30min_loop(self):
        """선택된 시간마다 이미지 서칭 및 조건 체크"""
        while self.monitor_running and not self.stop_flag:
            try:
                # 선택된 시간 대기
                minutes = self.monitor_interval // 60
                self.log(f"{minutes}분 대기 중...")
                time.sleep(self.monitor_interval)
                
                if self.stop_flag or not self.monitor_running:
                    break
                
                self.log(f"{minutes}분 경과 - 이미지 서칭 시작")
                
                # hidden.png와 saram.png 이미지 서치 (5초 간격으로 3회 시도)
                max_attempts = 3
                hidden_found_count = 0
                saram_found_count = 0
                
                for attempt in range(1, max_attempts + 1):
                    if self.stop_flag or not self.monitor_running:
                        break
                    
                    self.log(f"이미지 서칭 시도 {attempt}/{max_attempts}회")
                    
                    # hidden 이미지 서치
                    if search_image_only('hidden.png', threshold=0.5):
                        hidden_found_count += 1
                        self.log(f"hidden 발견 ({hidden_found_count}회)")
                    
                    # saram 이미지 서치
                    if search_image_only('saram.png', threshold=0.5):
                        saram_found_count += 1
                        self.log(f"saram 발견 ({saram_found_count}회)")
                    
                    # 마지막 시도가 아니면 5초 대기
                    if attempt < max_attempts:
                        time.sleep(5)
                
                # 3회 시도 결과 확인
                if hidden_found_count > 0 and saram_found_count > 0:
                    # 둘 다 최소 1회 이상 발견됨
                    self.log("hidden과 saram 둘 다 발견 - 대기 계속")
                    continue
                
                # 둘 중 하나라도 발견되지 않음 - 매크로 재시작
                self.log(f"이미지 미발견 (hidden: {hidden_found_count}회, saram: {saram_found_count}회) - 매크로 재시작")
                
                # 한게임/엠게임 체크에 따라 매크로 재실행
                if self.hangame_var.get():
                    thread = threading.Thread(target=self.start_hangame)
                    thread.daemon = True
                    thread.start()
                elif self.mgame_var.get():
                    thread = threading.Thread(target=self.start_mgame)
                    thread.daemon = True
                    thread.start()
                
                # 모니터링 계속
                continue
            
            except Exception as e:
                self.log(f"모니터링 중 오류: {e}")
                time.sleep(60)  # 오류 시 1분 대기 후 재시도
    
    def restart_game_process(self):
        """게임 강제종료 및 start.bat 실행"""
        try:
            print("귀혼 게임 강제종료 시작")
            # 게임 프로세스 종료 (일반적인 게임 프로세스명, 필요시 수정)
            subprocess.run(['taskkill', '/F', '/IM', 'hon.exe'], capture_output=True)
            subprocess.run(['taskkill', '/F', '/IM', 'game.exe'], capture_output=True)
            time.sleep(2)
            
            # macro 폴더의 start.bat 관리자권한으로 실행
            script_dir = os.path.dirname(os.path.abspath(__file__))
            bat_path = os.path.join(script_dir, 'start.bat')
            
            if os.path.exists(bat_path):
                print(f"start.bat 관리자권한 실행: {bat_path}")
                # PowerShell을 사용하여 관리자권한으로 실행
                subprocess.Popen([
                    'powershell',
                    '-Command',
                    f"Start-Process '{bat_path}' -Verb RunAs"
                ], shell=True)
                
                # 10초 대기
                print("start.bat 실행 후 10초 대기")
                time.sleep(10)
                
                # hellper 이미지 서치 (최대 3회 시도, 10초 간격)
                print("hellper 이미지 서치 중...")
                hellper_found = False
                max_attempts = 3
                
                for attempt in range(1, max_attempts + 1):
                    if self.stop_flag or not self.monitor_running:
                        break
                    
                    print(f"hellper 검색 시도 {attempt}/{max_attempts}회")
                    hellper_found = search_image_only('hellper.png', threshold=0.5)
                    
                    if hellper_found:
                        print(f"hellper 발견 ({attempt}회 시도) - 매크로 로직 시작")
                        break
                    
                    # 마지막 시도가 아니면 10초 대기
                    if attempt < max_attempts:
                        print(f"hellper 미발견, 10초 후 재시도...")
                        time.sleep(10)
                
                # hellper 발견 시에만 매크로 시작
                if hellper_found:
                    print("hellper 발견 - 매크로 로직 시작")
                    self.log("hellper 발견 - 매크로 로직 시작")
                    
                    # 한게임/엠게임 접속
                    if self.hangame_var.get():
                        thread = threading.Thread(target=self.start_hangame)
                        thread.daemon = True
                        thread.start()
                    elif self.mgame_var.get():
                        thread = threading.Thread(target=self.start_mgame)
                        thread.daemon = True
                        thread.start()
                else:
                    print(f"hellper 미발견 ({max_attempts}회 시도 실패) - 매크로 시작 안함")
                    self.log(f"hellper {max_attempts}회 시도 실패 - 매크로 시작 안함")
            else:
                print(f"start.bat 파일을 찾을 수 없습니다: {bat_path}")
        
        except Exception as e:
            print(f"게임 재시작 중 오류: {e}")
    
    def run_local_start_bat(self):
        """바탕화면의 macro 폴더 내 start.bat 파일을 관리자 권한으로 실행"""
        try:
            # 바탕화면의 macro 폴더 경로
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            bat_path = os.path.join(desktop, "macro", "start.bat")
            
            if os.path.exists(bat_path):
                self.log(f"start.bat 관리자권한 실행: {bat_path}")
                # PowerShell을 사용하여 관리자권한으로 실행
                subprocess.Popen([
                    'powershell',
                    '-Command',
                    f"Start-Process '{bat_path}' -Verb RunAs"
                ], shell=True)
            else:
                self.log(f"바탕화면의 macro 폴더에 start.bat 파일을 찾을 수 없습니다: {bat_path}")
        
        except Exception as e:
            self.log(f"start.bat 실행 중 오류: {e}")
    
    def run_desktop_start_bat(self):
        """바탕화면의 start.bat 파일을 관리자 권한으로 실행"""
        try:
            # 바탕화면 경로 가져오기
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            bat_path = os.path.join(desktop, "start.bat")
            
            if os.path.exists(bat_path):
                self.log(f"start.bat 관리자권한 실행: {bat_path}")
                # PowerShell을 사용하여 관리자권한으로 실행
                subprocess.Popen([
                    'powershell',
                    '-Command',
                    f"Start-Process '{bat_path}' -Verb RunAs"
                ], shell=True)
            else:
                self.log(f"바탕화면에 start.bat 파일을 찾을 수 없습니다: {bat_path}")
        
        except Exception as e:
            self.log(f"start.bat 실행 중 오류: {e}")
    
    def run(self):
        """GUI를 실행합니다."""
        self.root.mainloop()

if __name__ == "__main__":
    app = MoneyPatcher()
    app.run()

