# [AI-Assisted Application Configuration Tool](https://github.com/ardafincan/ai-assisted-config-tool)
##### By Ali Arda Fincan

## Contents: 
1. [General Look to Project](#general-look-to-project)
2. [User Request Data-Flow](#user-request-data-flow)
3. [Service Communication Flow](#service-communication-flow)
4. [Design Process and Trade-offs](#design-decisions-and-trade-offs)

## General Look to Project

This is an AI-Assisted Local Configuration Management Tool that allows users to modify application configurations using natural language instead of editing JSON files or writing some query for it. 

#### Core Purpose
Users cand send plain-English requests like: 
- "set tournament service memory to 1024mb"
- "increase chat replicas by 2"

The system uses Large Language Models to understand users intent and return the changed JSON of intended applications configuration. 

#### System Requirements
- Min. 15GB memory for Docker or 18GB for safety (peak usage + 20%)
- If host machine has Nvidia-GPU and Nividia-Container-Toolkit please uncomment stated part at docker-compose.yml for significant performance gain.

## User Request Data-Flow
1. User sends a request to exposed port of `bot-service`(default 5003) from host machine. 
2. `bot-service` takes request and gives input message to `ollama-service` container for **Qwen3:0.6b** model to analyze input and decide which one is the intended application. 
3. `bot-service` sends a request to `schema-service` in order to retrieve JSON-schema of application to change.
4. `bot-service` sends a request to `value-service` in order to retrieve current values JSON of application to change.
5. `bot-service` sends a request to `ollama-service` with schema and value JSONs in order to take updated values JSON as response. **Llama3.1:8b** is used in this state.
6. `bot-service` takes response from `ollama-service` and validates the new JSON with original schema. 
7. `bot-service` returns the updated values JSON to user. 

## Service Communication Flow
Since `bot-service` has the only I/O port exposed to outside, it controls main communication. Any other service does not directly communicate with each other and this helps following effects of code changes in a service. 

As explained at the previous section, we can show the communication flow as following: 
- `bot-service` ---input_message---> `ollama-service`
- `ollama-service` ---app_name---> `bot-service`
- `bot-service` ---app_name---> `schema-service` & `value-service`
- `schema-service` ---JSON Schema---> `bot-service`
- `value-service` ---JSON Values---> `bot-service` 
- `bot-service` ---JSON Schema & values & input_message---> `ollama-service`
- `ollama-service` ---updated_values JSON---> `bot-service`

## Design Decisions and Trade-offs
#### How to Select Right LLM? 
I haven't worked on getting structured outputs from LLMs before, so I started with some research. According to *StructEval: Benchmarking LLMs’ Capabilities to Generate Structural Outputs* from Yang et al. **Qwen3:4b** was best model among other models they tested(open-source models with parameter size between 3.8-8 billions). Given the thinking capability of Qwen3 family that sounds a reasonable model to try. I decided using **Qwen3:0.6b** for finding application name and **Qwen3:8b** for updating values. But after some experiments with given examples I saw that Qwen3:4b was not the right model for this job. And I decided I should go up for ~8B models so I had three strong candidates for this job: **Qwen3:8b**, **Gemma3:12B** and **Llama3.1:8B**. After comparing their results with given examples and synthetic ones I created using *Claude Sonnet4.5*, and the best result was **Llama3.1:8B** with perfect accuracy. So I decided going with **Qwen3:0.6b** for getting *app_name* and **Llama3.1:8B** for getting the *updated_values*. Using two seperate models may need more memory consumption but I assumed that a system like this will be run on a machine which is at least powerfull than a consumer computer and since small model is really small the extra-memory usage can be ignored. This makes a great win in terms of speed, running a 8B model for just getting app_name would be much slower and we can simply test this by looking at TTFT(Time To First Token) metric of two models.

Note: Even though I thing using an LLM might be unccessary for getting application name, I used it because of given directives wanted it. I think this problem can be solved with a small machine-learning model with some synthetic data or even maybe algorithmicly with text-matching.

#### Why Flask over FastAPI? 
I was going for FastAPI but starting a server using python and getting arguments at start is easier using Flask. Because we need to use uvicorn or hypercorn but since Flask has a built-in development server it was much simpler to build on Flask.

#### Adding GPU Support or Not? 
Since LLM inference is mainly composed of large number of matrix operations, using a GPU for this purpose makes huge speed differences. So I wanted to add GPU support for Ollama container but I am not sure if the host machine this project will be run has Nvidia GPU and Nvidia-Container-Toolkit installed. Because of this I have commented out that part in docker-compose.yml file and if the person who runs this project may use GPU for LLM inference simply by uncommenting stated lines. I also wanted to add support for Apple Metal Performance Shaders(MPS) but I see that Docker containers don't have direct access to Metal framework yet. 

#### Docker & Deployment
The healthchecks may be the part that gave me the most trouble. After struggling a while I have managed to fix everything. But there was a problem, the healthcheck for ollama-service was sending `ollama list` requests to service and it works at the first moment ollama gets served. So user was able to send requests to bot-service but this is not a desired state, I had to show bot-service as healthy after both models was pulled completely. So I found a way, I started listing existing models and checking if both models are in the output. So bot-service only sees the ollama-service as healthy after both necessary models are pulled. This means user can send requests right after bot-service is healthy. 
 
