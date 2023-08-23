var NodeHelper = require("node_helper");
const socketIO = require('socket.io');
const { exec } = require('child_process'); // 추가

module.exports = NodeHelper.create({
    start: function () {
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
        car1 = "";
        car2 = "";
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
                    console.log('라디오 재생')
                    this.sendSocketNotification("UPDATE_TEXT", 'play radio');
                }
                else if(obj == 'stop_radio')
                {
                    this.Stop_Radio();
                    console.log('라디오 중지')
                    this.sendSocketNotification("UPDATE_TEXT", 'stop radio');
                }
            })

            socket.on('car', (obj) => {
                console.log('Server car received data:', obj);

                io.to(car2).emit('start', obj);
            })

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
    }
});
