import { useState } from "react";
import Home     from "./screens/Home";
import Capture  from "./screens/Capture";
import AudioTest from "./screens/AudioTest";
import Results  from "./screens/Results";
import Loading  from "./screens/Loading";

export default function App() {
  const [screen,  setScreen]  = useState("home");
  const [imageFile, setImageFile] = useState(null);
  const [audioBlob, setAudioBlob] = useState(null);
  const [description, setDescription] = useState("");
  const [result,  setResult]  = useState(null);

  const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

  async function submitAssessment(imgFile, audBlob) {
    setScreen("loading");
    try {
      const fd = new FormData();
      fd.append("image", imgFile, "jewelry.jpg");
      if (audBlob) fd.append("audio", audBlob, "tap.wav");
      if (description.trim()) fd.append("description", description.trim());

      const res  = await fetch(`${API}/assess`, { method: "POST", body: fd });
      const data = await res.json();
      setResult(data);
      setScreen("results");
    } catch (e) {
      alert("Server error: " + e.message);
      setScreen("capture");
    }
  }

  const go = (s) => setScreen(s);

  return (
    <>
      {screen === "home"    && <Home     onStart={() => go("capture")} />}
      {screen === "capture" && (
        <Capture
          onCapture={(f) => { setImageFile(f); go("audio"); }}
          onBack={() => go("home")}
          description={description}
          setDescription={setDescription}
        />
      )}
      {screen === "audio"   && (
        <AudioTest
          onDone={(blob) => {
            setAudioBlob(blob);
            submitAssessment(imageFile, blob);
          }}
          onSkip={() => submitAssessment(imageFile, null)}
          onBack={() => go("capture")}
        />
      )}
      {screen === "loading" && <Loading />}
      {screen === "results" && (
        <Results
          result={result}
          onReset={() => {
            setImageFile(null);
            setAudioBlob(null);
            setResult(null);
            go("home");
          }}
        />
      )}
    </>
  );
}
