import { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Volume2, Loader2, Send, FileText, Clock } from 'lucide-react';
import { useSituationGraph } from '../hooks/useSituationGraph';

export function VoicePage() {
  const { voiceReports } = useSituationGraph();
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [campName, setCampName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPlayingReport, setIsPlayingReport] = useState(false);
  const [reportText, setReportText] = useState('');
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  function startRecording() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setTranscript('[Speech recognition not supported in this browser. Please type your report below.]');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    let finalTranscript = '';

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript + ' ';
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      setTranscript(finalTranscript + interim);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
    setTranscript('');
  }

  function stopRecording() {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsRecording(false);
  }

  async function submitTranscript() {
    if (!transcript.trim()) return;
    setIsSubmitting(true);
    try {
      const res = await fetch('/api/voice/transcribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: transcript.trim(),
          camp_name: campName || undefined,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setTranscript('');
      setCampName('');
    } catch (e) {
      console.error('Failed to submit transcript:', e);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function generateAndPlayReport() {
    setIsLoadingReport(true);
    try {
      // First get the report text
      const textRes = await fetch('/api/voice/report');
      if (!textRes.ok) throw new Error(`HTTP ${textRes.status}`);
      const { report_text } = await textRes.json();
      setReportText(report_text);

      // Then try TTS
      try {
        const audioRes = await fetch('/api/voice/synthesize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: report_text }),
        });

        if (audioRes.ok) {
          const blob = await audioRes.blob();
          const url = URL.createObjectURL(blob);
          const audio = new Audio(url);
          audioRef.current = audio;
          audio.onended = () => {
            setIsPlayingReport(false);
            URL.revokeObjectURL(url);
          };
          audio.play();
          setIsPlayingReport(true);
        }
      } catch {
        // TTS failed (no API key probably), just show text
        console.log('TTS not available, showing text only');
      }
    } catch (e) {
      console.error('Failed to generate report:', e);
    } finally {
      setIsLoadingReport(false);
    }
  }

  function stopReport() {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsPlayingReport(false);
  }

  return (
    <div className="flex flex-col h-full bg-[#0a0a0f] overflow-hidden">
      {/* Sub-header */}
      <div className="border-b border-[#27272a] px-6 py-3 flex items-center justify-between flex-shrink-0 bg-[#0d0d14]">
        <div className="flex items-center gap-3">
          <Mic className="w-4 h-4 text-green-400" />
          <span className="text-zinc-200 text-sm font-semibold">Voice Command Center</span>
          <span className="text-zinc-600 text-xs">— TTS Reports + Voice Input</span>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">

          {/* Situation Report TTS */}
          <div className="border border-[#27272a] rounded-xl bg-[#12121a] p-6">
            <div className="flex items-center gap-2 mb-4">
              <Volume2 className="w-5 h-5 text-amber-400" />
              <h2 className="text-zinc-200 font-semibold">Situation Report</h2>
              <span className="text-zinc-600 text-xs">— AI-generated spoken briefing</span>
            </div>

            <div className="flex items-center gap-3 mb-4">
              {!isPlayingReport ? (
                <button
                  onClick={generateAndPlayReport}
                  disabled={isLoadingReport}
                  className="flex items-center gap-2 px-5 py-3 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 rounded-lg font-medium transition-colors disabled:opacity-40"
                >
                  {isLoadingReport ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Volume2 className="w-4 h-4" />
                  )}
                  {isLoadingReport ? 'Generating...' : 'Play Situation Report'}
                </button>
              ) : (
                <button
                  onClick={stopReport}
                  className="flex items-center gap-2 px-5 py-3 bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-300 rounded-lg font-medium transition-colors"
                >
                  <Volume2 className="w-4 h-4" />
                  Stop
                </button>
              )}
            </div>

            {reportText && (
              <div className="bg-[#1a1a25] border border-[#27272a] rounded-lg p-4">
                <p className="text-sm text-zinc-300 leading-relaxed">{reportText}</p>
              </div>
            )}
          </div>

          {/* Voice Recorder */}
          <div className="border border-[#27272a] rounded-xl bg-[#12121a] p-6">
            <div className="flex items-center gap-2 mb-4">
              <Mic className="w-5 h-5 text-green-400" />
              <h2 className="text-zinc-200 font-semibold">Field Report Input</h2>
              <span className="text-zinc-600 text-xs">— Record or type field reports</span>
            </div>

            {/* Camp Name */}
            <div className="mb-4">
              <label className="text-xs text-zinc-500 mb-1 block">Camp/Location Name (optional)</label>
              <input
                type="text"
                value={campName}
                onChange={(e) => setCampName(e.target.value)}
                placeholder="e.g., Sector 2 Relief Camp"
                className="w-full bg-[#1a1a25] border border-[#27272a] rounded-lg px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 outline-none focus:border-zinc-500"
              />
            </div>

            {/* Record Button */}
            <div className="flex items-center gap-4 mb-4">
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${
                  isRecording
                    ? 'bg-red-500/30 border-2 border-red-500 text-red-300 pulse-critical'
                    : 'bg-green-500/20 border-2 border-green-500/50 text-green-400 hover:bg-green-500/30'
                }`}
              >
                {isRecording ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
              </button>
              <div>
                <p className="text-sm text-zinc-300">
                  {isRecording ? 'Recording... Click to stop' : 'Click to start voice recording'}
                </p>
                <p className="text-xs text-zinc-600">
                  {isRecording ? 'Speak clearly about the field situation' : 'Or type your report below'}
                </p>
              </div>
            </div>

            {/* Transcript Area */}
            <textarea
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder="Voice transcript will appear here, or type your field report..."
              rows={4}
              className="w-full bg-[#1a1a25] border border-[#27272a] rounded-lg px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 resize-none outline-none focus:border-zinc-500 mb-3"
            />

            {/* Submit */}
            <button
              onClick={submitTranscript}
              disabled={!transcript.trim() || isSubmitting}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/40 text-blue-300 rounded-lg text-sm font-medium transition-colors disabled:opacity-40"
            >
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Submit Report to Situation Graph
            </button>
          </div>

          {/* Recent Voice Reports */}
          <div className="border border-[#27272a] rounded-xl bg-[#12121a] p-6">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="w-5 h-5 text-zinc-400" />
              <h2 className="text-zinc-200 font-semibold">Recent Voice Reports</h2>
              <span className="text-zinc-500 text-xs">({voiceReports.length})</span>
            </div>

            {voiceReports.length > 0 ? (
              <div className="space-y-3">
                {voiceReports.map((report) => (
                  <div key={report.id} className="bg-[#1a1a25] border border-[#27272a] rounded-lg p-3 slide-in">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-zinc-500">{report.id}</span>
                        {report.camp_name && (
                          <span className="text-xs text-green-400 bg-green-500/10 px-1.5 py-0.5 rounded">
                            {report.camp_name}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-1 text-zinc-600 text-xs">
                        <Clock className="w-3 h-3" />
                        {new Date(report.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                    <p className="text-sm text-zinc-300 line-clamp-2">{report.transcript}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-zinc-600 py-6 text-xs">
                No voice reports yet. Record or type a field report above.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
