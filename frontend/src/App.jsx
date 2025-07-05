import { useRef, useState, useEffect, useLayoutEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Legend);

function App() {
  const [story, setStory] = useState('');
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [progressStage, setProgressStage] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [jobId, setJobId] = useState(null);
  const [emotionData, setEmotionData] = useState(null);
  const [showTimeline, setShowTimeline] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const audioRef = useRef(null);
  const chartRef = useRef(null);

  const emotionToColor = (emotion) => {
  switch (emotion.toLowerCase()) {
    case "joy": return "rgb(251, 191, 36)";
    case "sadness": return "rgb(59, 130, 246)";
    case "anger": return "rgb(239, 68, 68)";
    case "fear": return "rgb(132, 204, 22)";
    case "surprise": return "rgb(14, 165, 233)";
    case "love": return "rgb(236, 72, 153)";
    default: return "rgb(148, 163, 184)";
    }
  };

  useEffect(() => {
    const savedStory = localStorage.getItem("emovox-story");
    if (savedStory) {
      setStory(savedStory);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("emovox-story", story);
  }, [story]);

  const handleSampleSubmit = (text) => {
    setStory(text);
    setShouldScrollToDemo(true);
    handleSubmit(null, text);
  };

  const demoRef = useRef(null);
  const [shouldScrollToDemo, setShouldScrollToDemo] = useState(false);

  useEffect(() => {
    if (audioUrl) {
      const audioSection = document.getElementById("audio-player");
      if (audioSection) {
        audioSection.scrollIntoView({ behavior: "smooth" });
      }
    }
  }, [audioUrl]);

  useLayoutEffect(() => {
    if (shouldScrollToDemo && demoRef.current) {
      demoRef.current.scrollIntoView({ behavior: 'smooth' });
      setShouldScrollToDemo(false);
    }
  }, [shouldScrollToDemo]);

  const handleSubmit = async (e = null, customStory = null) => {
    if (e?.preventDefault) e.preventDefault();

    const storyToSubmit = customStory ?? story;

    setLoading(true);
    setAudioUrl(null);
    setProgressStage(0);
    setProgressMessage('');

    try {
      const response = await fetch('http://localhost:5000/api/story', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ story: storyToSubmit }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit story');
      }

      const { progress_id } = await response.json();
      const eventSource = new EventSource(`http://localhost:5000/api/progress/${progress_id}`);

      eventSource.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('SSE received:', data);

          // Update progress message
          if (data.message) {
            setProgressMessage(data.message);
          }

          // Update progress stage based on the stage
          if (data.stage === 'init') {
            setProgressStage(0);
          } else if (data.stage === 'emotion') {
            setProgressStage(1);
          } else if (data.stage === 'tts') {
            setProgressStage(2);
          } else if (data.stage === 'mixing') {
            setProgressStage(3);
          }

          // Handle completion
          if (data.stage === 'done') {
            eventSource.close();
            setLoading(false);
            
            try {
              const audioResponse = await fetch(`http://localhost:5000/api/audio/${progress_id}`);
              if (!audioResponse.ok) {
                throw new Error("Failed to fetch audio");
              }

              const audioBlob = await audioResponse.blob();
              const audioUrl = URL.createObjectURL(audioBlob);
              setAudioUrl(audioUrl);

              const emotionResponse = await fetch(`http://localhost:5000/api/emotions/${progress_id}`);
              if (emotionResponse.ok) {
                const emotionJson = await emotionResponse.json();
                setEmotionData(emotionJson);
              }

              
              console.log('Audio URL set:', audioUrl);
            } catch (err) {
              console.error("Error fetching audio:", err);
              alert("Audio generation completed but failed to load audio file.");
            }
          }

          // Handle errors
          if (data.stage === 'error') {
            eventSource.close();
            setLoading(false);
            alert(`Error: ${data.message}`);
          }
        } catch (parseError) {
          console.error('Error parsing SSE data:', parseError);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        eventSource.close();
        setLoading(false);
        alert('Connection error during processing.');
      };

    } catch (error) {
      console.error("Error:", error);
      alert("Failed to send story to server.");
      setLoading(false);
    }
  };

  const progressMessages = [
    "Analyzing emotional context...",
    "Generating adaptive voice...",
    "Composing background music...",
    "Finalizing audio export..."
  ];

  const features = [
    {
      icon: <div className="w-8 h-8 text-cyan-400 text-2xl"></div>,
      title: "Emotion Detection",
      description: "Advanced AI analyzes emotional context and tone in your stories"
    },
    {
      icon: <div className="w-8 h-8 text-sky-400 text-2xl"></div>,
      title: "Dynamic Voice Synthesis",
      description: "Voice modulation that matches the emotional intensity of your narrative"
    },
    {
      icon: <div className="w-8 h-8 text-blue-400 text-2xl"></div>,
      title: "Adaptive Music Scoring",
      description: "Background music that evolves with your story's emotional journey"
    },
    {
      icon: <div className="w-8 h-8 text-indigo-400 text-2xl"></div>,
      title: "Real-time Processing",
      description: "Instant audio generation with professional-quality output"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950">

      <div className="w-full text-center py-3 bg-gradient-to-r from-blue-700 to-cyan-600 text-white font-semibold">
        Only short stories
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-blue-900/20 backdrop-blur-md border-b border-cyan-400/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold text-white">Emovox</span>
            </div>
            <div className="hidden md:flex space-x-8">
              <a href="#hero" className="text-cyan-200 hover:text-white transition-colors">Home</a>
              <a href="#features" className="text-cyan-200 hover:text-white transition-colors">Features</a>
              <a href="#demo" className="text-cyan-200 hover:text-white transition-colors">Try Now</a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section id="hero" className="pt-32 pb-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center px-4 py-2 bg-blue-500/20 rounded-full text-cyan-200 text-sm mb-8 backdrop-blur-sm border border-cyan-400/30">
            AI-Powered Emotional Storytelling
          </div>
          <h1 className="text-6xl md:text-7xl font-extrabold text-white mb-6 tracking-tight">
            <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-600 bg-clip-text text-transparent">
              Emovox
            </span>
          </h1>
          <p className="text-xl text-cyan-100 mb-12 max-w-3xl mx-auto leading-relaxed">
            Transform your written stories into immersive audio experiences with emotion-aware voice synthesis 
            and adaptive musical scoring. Powered by cutting-edge AI technology.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button 
              onClick={() => document.getElementById('demo').scrollIntoView({ behavior: 'smooth' })}
              className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-full font-semibold hover:scale-105 transform transition duration-200 shadow-lg hover:shadow-cyan-500/25"
            >
              Create Your own Story <span className="ml-2">→</span>
            </button>
          </div>
        </div>
      </section>

      {/* Sample Stories Section */}
      <section className="py-16 px-4 bg-blue-950/40 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6">Try a Sample Story</h2>
          <p className="text-cyan-100 mb-10">Choose a story and see it come to life.</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 gap-y-10 justify-items-center">
            {[
              `The sunlight spilled through her open window.\nShe spun in circles, arms wide, laughing at the sky.\nA breeze swept in, carrying the scent of jasmine.\nIt felt like the whole world was dancing with her.`,
              `The letter was yellowed and folded with care.\nHe read the words again, lips silently moving.\nTears blurred the ink as memories flooded in.\nHe held it close, as if it were her hand.`,
              `The power cut out, and silence fell.\nFootsteps echoed from upstairs — but no one lived there.\nHer breath caught as the doorknob began to turn.\nShe wasn't alone in the house anymore.`,
              `The vase shattered as it hit the floor.\nHe stormed out, the sound of his footsteps sharp and final.\nShe stood frozen, fists clenched at her sides.\nNo words could mend what rage had torn open.`,
            ].map((text, idx) => (
              <button
                key={idx}
                onClick={() => handleSampleSubmit(text)}
                disabled={loading}
                className="p-6 max-w-md w-full bg-gradient-to-br from-blue-800 to-indigo-800 text-white rounded-2xl hover:scale-105 transition transform duration-200 border border-cyan-400/20 shadow-md hover:shadow-cyan-500/20 whitespace-pre-line text-left leading-relaxed disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {text}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section id="demo" ref={demoRef} className="py-24 px-4 bg-blue-950/30 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-5xl font-bold text-white mb-6">Create Your own Story</h2>
            <p className="text-xl text-cyan-100">
              Experience the magic of emotion-aware storytelling. Enter your story and hear it come to life.
            </p>
          </div>
          
          <div className="bg-gradient-to-br from-blue-900/40 to-indigo-900/40 backdrop-blur-lg rounded-3xl p-8 shadow-2xl border border-cyan-400/30">
            <div className="space-y-6">
              <div>
                <label className="block text-white font-medium mb-3">Your Story</label>
                <textarea 
                  id="story"
                  rows="8"
                  className="w-full p-6 bg-blue-900/30 border border-cyan-400/30 rounded-2xl focus:outline-none focus:ring-2 focus:ring-cyan-400 text-white placeholder-cyan-200/50 resize-none backdrop-blur-sm"
                  placeholder="Once upon a time, in a world where emotions could be heard in every word..."
                  value={story}
                  onChange={(e) => setStory(e.target.value)}
                />
              </div>

              <button
                onClick={handleSubmit}
                disabled={loading || !story.trim()}
                className="w-full py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-2xl font-semibold hover:scale-105 transform transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-lg hover:shadow-cyan-500/25"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-3"></div>
                    Sit back and relax, it may take a while...
                  </span>
                ) : (
                  <span className="flex items-center justify-center">
                    Generate Emotional Audio
                  </span>
                )}
              </button>
            </div>

            {loading && (
              <div className="mt-8">
                <div className="w-full bg-blue-900/40 rounded-full h-3 mb-4 overflow-hidden">
                  <div className="bg-gradient-to-r from-cyan-500 to-blue-600 h-3 rounded-full animate-pulse transition-all duration-1000" 
                       style={{ width: `${((progressStage + 1) / progressMessages.length) * 100}%` }} />
                </div>
                <div className="text-center text-cyan-200 text-sm space-y-2">
                  {progressMessage && <p className="text-cyan-300 font-medium">{progressMessage}</p>}
                  {progressMessages.slice(0, progressStage + 1).map((msg, idx) => (
                    <p key={idx} className={idx === progressStage ? "text-white font-medium" : "text-cyan-400"}>
                      {msg}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {audioUrl && (
  <div id="audio-player" className="mt-8 space-y-6">
    <div className="bg-blue-900/40 rounded-2xl p-6 backdrop-blur-sm border border-cyan-400/20">
      <h3 className="text-white font-semibold mb-4 flex items-center">
        <span className="mr-2 text-cyan-400">✓</span>
        Your Story is Ready!
      </h3>
      <audio
        ref={audioRef}
        controls
        src={audioUrl}
        className="w-full rounded-lg bg-blue-900/30 backdrop-blur-sm"
        onRateChange={() => setPlaybackRate(audioRef.current.playbackRate)}
      />
      <div className="mt-4 flex items-center gap-4">
        <label className="text-cyan-100">Speed:</label>
        <select
          className="bg-blue-800 text-white rounded px-3 py-1"
          value={playbackRate}
          onChange={(e) => {
            const rate = parseFloat(e.target.value);
            setPlaybackRate(rate);
            if (audioRef.current) audioRef.current.playbackRate = rate;
          }}
        >
          <option value={0.5}>0.5x</option>
          <option value={1}>1x</option>
          <option value={1.5}>1.5x</option>
          <option value={2}>2x</option>
        </select>
      </div>
    </div>

    <div className="flex flex-col sm:flex-row gap-4">
      <a
        href={audioUrl}
        download="emotional_story.wav"
        className="flex-1 px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-xl font-semibold hover:scale-105 transform transition duration-200 text-center shadow-lg hover:shadow-cyan-500/25"
      >
        <span className="mr-2">↓</span>
        Download Audio
      </a>
      <button
        onClick={() => setShowTimeline(!showTimeline)}
        className="flex-1 px-6 py-3 bg-cyan-700 text-white rounded-xl font-semibold hover:bg-cyan-600 transition duration-200 backdrop-blur-sm border border-cyan-400/30"
      >
        {showTimeline ? "Hide Emotional Timeline" : "Show Emotional Timeline"}
      </button>
    </div>

    {showTimeline && emotionData && (
      <div className="mt-8 bg-blue-900/30 p-6 rounded-2xl border border-cyan-400/20">
        <div className="flex justify-end gap-4 mb-4">
  <button
    onClick={() => {
      if (chartRef.current) {
        const url = chartRef.current.toBase64Image();
        const link = document.createElement("a");
        link.href = url;
        link.download = "emotion_timeline.png";
        link.click();
      }
    }}
    className="px-4 py-2 bg-cyan-600 text-white rounded hover:bg-cyan-500"
  >
    Export as PNG
  </button>

  <button
    onClick={() => {
      const csvHeader = "Sentence,Emotion\n";
      const csvRows = emotionData.sentences.map((sentence, i) =>
        `"${sentence.replace(/"/g, '""')}",${emotionData.emotions[i]}`
      );
      const csvContent = csvHeader + csvRows.join("\n");

      const blob = new Blob([csvContent], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "emotion_timeline.csv";
      link.click();
    }}
    className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-500"
  >
    Download CSV
  </button>
</div>

<Line
 ref={(chart) => {
  if (chart) chartRef.current = chart.chartInstance ?? chart;
}}
  data={{
    labels: emotionData.sentences.map((_, i) => `S${i + 1}`),
    datasets: [
      {
        label: "Emotion per Sentence",
        data: emotionData.emotions,
        backgroundColor: emotionData.emotions.map(emotionToColor),
        borderColor: "#3b82f6",
        borderWidth: 1,
        pointRadius: 5,
        pointHoverRadius: 8,
        fill: false,
        tension: 0.3
      }
    ]
  }}
  options={{
    responsive: true,
    scales: {
      y: {
        type: "category",
        labels: [...new Set(emotionData.emotions)],
        title: { display: true, text: "Emotion" }
      },
      x: { title: { display: true, text: "Sentence" } }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function (ctx) {
            const index = ctx.dataIndex;
            const sentence = emotionData.sentences[index];
            const emotion = emotionData.emotions[index];
            return [`Sentence: "${sentence}"`, `Emotion: ${emotion}`];
          }
        }
      }
    }
  }}
/>

      </div>
    )}
  </div>
)}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center relative -top-16 mb-16">
            <p className="text-xl text-cyan-100 max-w-2xl mx-auto">
              Our proprietary emotion detection engine analyzes your text and creates audio that truly captures the feeling behind your words.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="max-w-xs bg-gradient-to-br from-blue-900/40 to-indigo-900/40 backdrop-blur-sm rounded-2xl p-8 hover:bg-blue-800/50 transition-all duration-300 hover:scale-105 border border-cyan-400/20">
                <h3 className="text-xl font-semibold text-white mb-3">{feature.title}</h3>
                <p className="text-cyan-100 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 bg-blue-950/50 backdrop-blur-sm border-t border-cyan-400/20">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-2 mb-6">
            <span className="text-2xl font-bold text-white">Emovox</span>
          </div>
          <p className="text-cyan-200 mb-6">
            Bringing stories to life through emotion-aware AI technology
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;