from apify_client import ApifyClient


def run_apify(actor_url: str, run_input: dict, token: str):
    # url = f"https://api.apify.com/v2/actors/ACTOR_NAME_OR_ID/runs?token=YOUR_TOKEN"

    client = ApifyClient(token=token)

    # Run the Actor and wait for it to finish
    # .call method waits infinitely long using smart polling
    # Get back the run API object
    run = client.actor(actor_url).call(run_input=run_input)

    # Fetch and print Actor results from the run's dataset (if there are any)
    return client.dataset(run.default_dataset_id).iterate_items()
