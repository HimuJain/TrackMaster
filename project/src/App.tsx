import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Check, X } from 'lucide-react';

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingComplete, setRecordingComplete] = useState(false);
  const [audioData, setAudioData] = useState<Blob | null>(null);
  const [timer, setTimer] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [audioLevels, setAudioLevels] = useState<number[]>(Array(20).fill(0.15));
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number>();
  const chunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      analyserRef.current.fftSize = 256;
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const options = {
        mimeType: "audio/webm",
      };
      mediaRecorderRef.current = new MediaRecorder(stream, options);
      console.log("mimetype: ",mediaRecorderRef.current.mimeType)
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        chunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioData(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordingComplete(false);

      setTimer(0);
      timerIntervalRef.current = setInterval(() => {
        setTimer(prev => prev + 1);
      }, 1000);

      const updateAudioLevel = () => {
        analyserRef.current?.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((acc, val) => acc + val, 0) / bufferLength;
        const normalizedLevel = average / 256;
        setAudioLevel(normalizedLevel);
        
        setAudioLevels(prev => {
          const newLevels = [...prev];
          for (let i = 0; i < newLevels.length; i++) {
            const targetHeight = 0.15 + (normalizedLevel * 0.85);
            newLevels[i] = newLevels[i] + (targetHeight - newLevels[i]) * 0.3;
          }
          return newLevels;
        });
        
        animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
      };
      updateAudioLevel();
    } catch (err) {
      console.error('Error accessing microphone:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setRecordingComplete(true);
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      setAudioLevels(Array(20).fill(0.15));
    }
  };

  const handleSubmit = async () => {
    console.log('Submitting audio data:', audioData);
    setRecordingComplete(false);

    const formData = new FormData();

    formData.append("audio", audioData as Blob);
    formData.append("sample_rate", audioContextRef.current?.sampleRate || 44100);

    const response = await fetch("http://127.0.0.1:5000/classify_genre", {
      method: "POST",
      body: formData,
      mode: 'cors',
      // headers: {
      // "Content-Type": "multipart/form-data"
      // }
    }).then(resp => resp.text());

    console.log("Got a response");
    console.log(response);
    
    // reset things
    setAudioData(null);
    setTimer(0);

  };

  const handleDiscard = () => {
    setRecordingComplete(false);
    setAudioData(null);
    setTimer(0);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#3455d8] to-[#f78436] flex items-center justify-center p-4">
      <div className="flex flex-col gap-8 w-full max-w-2xl">
        {/* Main Recording Interface */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 flex items-center gap-6">
          {/* Record/Stop Button */}
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`group w-16 h-16 rounded-xl bg-white flex items-center justify-center transition-all duration-300 
              ${isRecording ? 'border-2 border-[#f78436]' : 'border-2 border-[#3455d8]'} 
              ${isRecording ? 'hover:bg-[#f78436]' : 'hover:bg-[#3455d8]'}`}
            disabled={recordingComplete}
          >
            {isRecording ? (
              <Square className="w-8 h-8 text-[#f78436] group-hover:text-white transition-colors duration-300" />
            ) : (
              <Mic className="w-8 h-8 text-[#3455d8] group-hover:text-white transition-colors duration-300" />
            )}
          </button>

          {/* Audio Visualization */}
          <div className="flex-1 h-16 flex items-center justify-center">
            <div className="flex gap-1 items-center">
              {audioLevels.map((level, i) => (
                <div
                  key={i}
                  className="w-2 bg-white rounded-full text-black"
                  // style={{
                  //   height: `${Math.max(15, level * 100)}%`
                  // }}
                >
                  <p>h</p>
                </div>
              ))}
            </div>
          </div>

          {/* Timer */}
          <div className="w-24 text-center">
            <span className="text-2xl font-mono text-white font-bold">
              {formatTime(timer)}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        {recordingComplete && (
          <div className="flex gap-4 justify-center">
            <button
              onClick={handleSubmit}
              className="group px-6 py-3 bg-white border-2 border-[#3455d8] hover:bg-[#3455d8] rounded-xl flex items-center gap-2 font-semibold transition-all duration-300"
            >
              <Check className="w-5 h-5 text-[#3455d8] group-hover:text-white transition-colors duration-300" />
              <span className="text-[#3455d8] group-hover:text-white transition-colors duration-300">Submit</span>
            </button>
            <button
              onClick={handleDiscard}
              className="group px-6 py-3 bg-white border-2 border-[#f78436] hover:bg-[#f78436] rounded-xl flex items-center gap-2 font-semibold transition-all duration-300"
            >
              <X className="w-5 h-5 text-[#f78436] group-hover:text-white transition-colors duration-300" />
              <span className="text-[#f78436] group-hover:text-white transition-colors duration-300">Discard</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;