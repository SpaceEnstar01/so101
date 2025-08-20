from huggingface_hub import HfApi

api = HfApi()
api.create_repo(
    repo_id="Enstar07/recodeTest",
    repo_type="dataset",
    exist_ok=True
)
