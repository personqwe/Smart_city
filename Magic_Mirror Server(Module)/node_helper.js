var NodeHelper = require("node_helper");
const socketIO = require('socket.io');
const { exec } = require('child_process'); // 추가
const fs = require('fs');
const sound = require('play-sound')(opts = {});

var musicFiles = [];
var musicFolder = '/root/MagicMirror/Music/';
var currentTrackIndex = 0;
var beepInProgress = false;
module.exports = NodeHelper.create({
    start: function () {
        car1 = "";
        car2 = "";
        this.File_Load();

        this.config = {};

        // Express 앱 생성
        const app = this.expressApp;

        // Express 앱을 이용하여 HTTP 서버 생성
        const server = require('http').Server(app);

        // socket.io 인스턴스를 생성하고 서버에 바인딩 (서버간 양방향 통신 설정)
        const io = socketIO(server);

        const port = 3000; 
        server.listen(port, () => {
            console.log(`Server is running on port ${port}`);
        });

        io.on('connection', (socket) => {
            console.log('Client connected');


            socket.on('car1', (obj) => {
                car1 = socket.id;
                if(car1 === socket.id)
                {
                    console.log('car1 id값 수신');
                }
            })
            socket.on('car2', (obj) => {
                car2 = socket.id;
                if(car2 === socket.id)
                {
                    console.log('car2 id값 수신');
                }
            })
            
            socket.on('radio', (obj) => {
                console.log('Server radio received data:', obj);

                // 추가: play_radio 데이터를 받으면 라디오 재생 명령 실행
                if (obj == 'play_radio') 
                {
                    this.Play_Radio();
                    console.log('라디오 재생');
                    this.sendSocketNotification("UPDATE_TEXT", 'play radio');
                }
                else if (obj == 'stop_radio') 
                {
                    this.Stop_Radio();
                    console.log('라디오 중지');
                }
            })

            socket.on('car', (obj) => {
                console.log('Server car received data:', obj);

                io.to(car2).emit('start', obj);
            })

            socket.on('Play_Music', (obj) =>{
                console.log('Play_Music:', obj);
                this.Play_Music();
            })

            socket.on('Next_Music', (obj) =>{
                currentTrackIndex++;
                if (currentTrackIndex >= musicFiles.length) {
                    currentTrackIndex = 0;
                }
                console.log('Next_Music:', obj);
                this.Play_Music();
                this.sendSocketNotification("UPDATE_TEXT", musicFiles[currentTrackIndex]);
            })

            socket.on('beep', (obj) => {
                if (!beepInProgress) { // 이미 beep가 진행 중인지 체크
                    beepInProgress = true; // 플래그를 true로 설정
                    console.log('정면에 장애물이 있습니다.', obj);
                    currentTrackIndex = 0;
                    this.Beep();
                    this.sendSocketNotification("UPDATE_TEXT", 'Beep');
                    // 일정 지연 시간 후에 또는 beep 재생이 끝났을 때 플래그를 다시 false로 설정
                    setTimeout(() => {
                        beepInProgress = false;
                        this.Stop_Radio();
                    }, 3000);
                }
            });

            socket.on('disconnect', () => {
                console.log('Client disconnected');
            });
        });
    },

    socketNotificationReceived: function (notification, payload) {
        if (notification === 'CONFIG') {
            this.sendSocketNotification('STARTED');
        }
        
    },

    Play_Radio: function () 
    {
        // 라디오 스트림 URL 설정
        const radioStreamUrl = 'http://ebsonairiosaod.ebs.co.kr/fmradiobandiaod/bandiappaac/playlist.m3u8';

        // vlc 명령 실행
        const command = `vlc ${radioStreamUrl} --play-and-exit`;

        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error(`Error executing vlc command: ${error}`);
            } else {
                console.log(`Radio playback started: ${radioStreamUrl}`);
            }
        });
    },
    Stop_Radio: function () {
        exec(`killall vlc`, (err, stdout, stderr) => {
            if (err) {
                console.error('Error stopping vlc:', err);
            } else {
                console.log('Stopped vlc:', stdout);
            }
        });
    },
    
    File_Load: function () { // Pass musicFolder as an argument
        fs.readdir(musicFolder, (err, files) => {
            if (!err) {
                musicFiles = files.filter(file => file.endsWith('.mp3'));
                console.log('파일 불러옴', musicFiles);
                if (musicFiles.length === 0) {
                    console.log('No music files found in the directory.');
                    return;
                }
            } else {
                console.error(`Error reading directory: ${err}`);
            }
        });
    },
    Play_Music: function () {
        this.Stop_Radio();
    
        if (musicFiles.length === 0) {
            console.log('음악 파일이 없습니다.');
            return;
        }
    
        const currentTrackPath = musicFolder + musicFiles[currentTrackIndex];
        const command = `vlc "${currentTrackPath}" --play-and-exit`;
    
        setTimeout(() => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    console.error(`Error executing vlc command: ${error}`);
                } else {
                    console.log(`Music playback started: ${currentTrackPath}`);
                }
            });
        }, 1000);  
    },
    Beep: function () {
        this.Stop_Radio();
    
        const currentTrackPath = "/root/MagicMirror/Beep/New project.mp3";
        const command = `vlc "${currentTrackPath}" --play-and-exit`;
    
        setTimeout(() => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    console.error(`Error executing vlc command: ${error}`);
                } else {
                    console.log(`Music playback started: ${currentTrackPath}`);
                }
            });
        }, 1000);  
    },
})
