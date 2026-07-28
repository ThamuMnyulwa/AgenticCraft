<span style="color:red; font-family:Helvetica Neue, Helvetica, Arial, sans-serif; font-size:2em;">An Exception was encountered at '<a href="#papermill-error-cell">In [1]</a>'.</span>

# MLflow for GenAI: Tracing a Gemini call

**Notebook 3 of 3** · Demo for the "MLflow: Autologging & Zero-Config" talk

Everything so far was classic ML: the unit of work is a **training run**. For LLMs and agents the unit of work changes to a **trace**, one end-to-end record of a prompt, the model call, tool use, tokens, and cost.

The good news: the ergonomics are the same. One line, `mlflow.gemini.autolog()`, and calls made through the Google GenAI SDK are captured as traces.

If you want to use Gemma 4 instead of a Gemini model, keep the same Gemini API client and set `GEMINI_MODEL` to a hosted Gemma model such as `gemma-4-26b-a4b-it` or `gemma-4-31b-it`. The environment variable is still `GEMINI_API_KEY` because hosted Gemma access is served through the Gemini API.

> This is a **teaser**. GenAI evaluation (`mlflow.genai.evaluate()` with LLM-as-judge scorers) and the Prompt Registry are whole topics of their own.

Find more at [thamu.dev](https://thamu.dev/).


## Setup

You need a Gemini API key in the `GEMINI_API_KEY` environment variable. Copy `.env.example` to `.env` and fill it in, or export the variable in your shell. Never hard-code the key in the notebook.

Use `GEMINI_MODEL=gemma-4-26b-a4b-it` for the Gemma 4 version of this demo. You can switch back to a Gemini model by changing only `GEMINI_MODEL`.


<span id="papermill-error-cell" style="color:red; font-family:Helvetica Neue, Helvetica, Arial, sans-serif; font-size:2em;">Execution using papermill encountered an exception here and stopped:</span>


```python
# uv:   !uv pip install "mlflow>=3.1" "google-genai>=1.21.0,<=2.8.0" python-dotenv
# pip:  !pip install "mlflow>=3.1" "google-genai>=1.21.0,<=2.8.0" python-dotenv

import os
from importlib.metadata import version

import mlflow
from dotenv import load_dotenv
from google import genai

load_dotenv()

print("mlflow       :", mlflow.__version__)
print("google-genai :", version("google-genai"))

assert os.environ.get("GEMINI_API_KEY"), (
    "Set GEMINI_API_KEY first, e.g. copy .env.example to .env and fill it in."
)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
print("model        :", GEMINI_MODEL)

```

    mlflow       : 3.14.0
    google-genai : 2.8.0



    ---------------------------------------------------------------------------

    AssertionError                            Traceback (most recent call last)

    Cell In[1], line 16
         12 
         13 print("mlflow       :", mlflow.__version__)
         14 print("google-genai :", version("google-genai"))
         15 
    ---> 16 assert os.environ.get("GEMINI_API_KEY"), (
         17     "Set GEMINI_API_KEY first, e.g. copy .env.example to .env and fill it in."
         18 )
         19 


    AssertionError: Set GEMINI_API_KEY first, e.g. copy .env.example to .env and fill it in.


## Step 1 — ML autolog vs GenAI autolog

Same idea, different target:

| | Traditional ML | GenAI |
|---|---|---|
| Unit of work | a training run | a prompt / trace |
| Turn it on | `mlflow.autolog()` | `mlflow.gemini.autolog()` |
| Captures | params, metrics, model | prompts, responses, latency, tokens |
| Evaluate | `mlflow.models.evaluate()` | `mlflow.genai.evaluate()` |

Note the two `evaluate` APIs are **not** interchangeable: `EvaluationMetric` objects only work with the ML evaluator, `Scorer` objects only with the GenAI one.


## Step 2 — Enable tracing and make a call

`mlflow.gemini.autolog()` turns on trace logging by default. Then use the Google GenAI client exactly as normal, and MLflow records the trace behind the scenes.



```python
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("genai-tracing-demo")
mlflow.gemini.autolog()   # one line: Gemini calls become traces

client = genai.Client()
response = client.models.generate_content(
    model=GEMINI_MODEL,
    contents="In one sentence, what is MLflow Tracing?",
)
print(response.text)

```

## Step 3 — Trace a small multi-step "app"

Real GenAI apps chain several calls. Wrap them in `@mlflow.trace` so the whole flow becomes one nested trace: you'll see each step, its inputs and outputs, and the total token cost.


```python
@mlflow.trace
def summarize_then_translate(text: str, language: str) -> str:
    summary = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"Summarize in one line: {text}",
    ).text

    translation = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"Translate to {language}: {summary}",
    ).text
    return translation

out = summarize_then_translate(
    "MLflow is an open-source platform for managing the ML and GenAI lifecycle.",
    "French",
)
print(out)

```

## Step 4 — View traces in the MLflow UI

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db   # macOS: add --port 5001 if 5000 is taken by AirPlay
```

Open the **genai-tracing-demo** experiment and click the **Traces** tab. For each trace you can inspect:
- the exact prompt and completion,
- latency per step,
- token usage where the Gemini response includes usage metadata,
- the nested structure of the multi-step call.

This is observability for LLM apps: the GenAI equivalent of comparing training runs.


## Recap

- GenAI keeps the one-line ergonomics: `mlflow.gemini.autolog()`.
- The unit of work is a **trace**, not a `fit()`, capturing prompts, responses, latency, and token metadata when available.
- `@mlflow.trace` groups a multi-step app into one nested trace.
- Same MLflow UI, same registry, same lineage as your ML work.

**Where to go next:** GenAI evaluation with LLM-as-judge scorers (`mlflow.genai.evaluate()`) and the versioned Prompt Registry.

That is the full set, thanks for following along. [thamu.dev](https://thamu.dev/)

