"use client";

import { useState, useEffect, useRef } from "react";

export function useMediaStream(camEnabled: boolean, micEnabled: boolean) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number | null>(null);

  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);

  // Initialize Media Stream
  useEffect(() => {
    async function setupMedia() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true,
        });

        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }

        // --- Audio Visualizer Setup ---
        const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
        const audioCtx = new AudioCtx();
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);

        audioContextRef.current = audioCtx;
        analyserRef.current = analyser;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const updateAudio = () => {
          if (!analyserRef.current) return;
          analyserRef.current.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
          }
          const average = sum / bufferLength;
          setAudioLevel(average / 128); // normalize 0 to 1ish
          animationRef.current = requestAnimationFrame(updateAudio);
        };

        updateAudio();
      } catch (err: any) {
        setPermissionError("We couldn't access your camera or microphone. Please check your browser permissions.");
      }
    }

    setupMedia();

    return () => {
      // Cleanup
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  // Sync state toggles with stream tracks
  useEffect(() => {
    if (streamRef.current) {
      streamRef.current.getVideoTracks().forEach(track => (track.enabled = camEnabled));
      streamRef.current.getAudioTracks().forEach(track => (track.enabled = micEnabled));
    }
  }, [camEnabled, micEnabled]);

  return { videoRef, permissionError, audioLevel };
}
