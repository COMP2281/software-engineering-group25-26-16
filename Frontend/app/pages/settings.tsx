import "../styles/pages.css";
import "../styles/dashboard.css";
import { Button } from "~/components/button";
import { useEffect, useState } from "react";

function Settings() {
  // get currently used model from backend
  const [loadedModel, setLoadedModel] = useState("Loading...");
  const [loadingNewModel, setLoadingNewModel] = useState(false);

  useEffect(() => {
    fetch("/api/settings/model")
      .then((response) => response.json())
      .then((data) => {
        setLoadedModel(data["model"]);
      });
  });

  const loadNewModel = () => {
    // get value from input field
    const newModel = (
      document.querySelector(".model_input") as HTMLInputElement
    ).value;

    setLoadingNewModel(true);
    fetch("/api/settings/model", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model: newModel }),
    })
      .then(() => {
        setLoadedModel(newModel);
      })
      .finally(() => {
        setLoadingNewModel(false);
      });
  };

  return (
    <div className="page_container h-screen w-full bg-[#f8fafc]">
      <header>
        <h1>Settings</h1>
      </header>

      {loadingNewModel && <p>Loading new model, this may take a while...</p>}
      {!loadingNewModel && (
        <i>
          Current model: <b>{loadedModel}</b>
        </i>
      )}

      <div className="input_wrapper">
        <input
          type="text"
          placeholder="Enter new model name"
          className="model_input"
        />
      </div>
      <Button onClick={loadNewModel} className="">
        Update Model
      </Button>
    </div>
  );
}

export default Settings;
