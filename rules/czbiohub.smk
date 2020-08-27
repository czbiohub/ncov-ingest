from os import environ
environ["GH_TOKEN"]      = config["gh_token"]      or ""
environ["GH_USERNAME"]   = config["gh_username"]   or ""
environ["SLACK_TOKEN"]   = config["slack_token"]   or ""
environ["SLACK_CHANNEL"] = config["slack_channel"] or ""
environ["AUGUR_RECURSION_LIMIT"] = str(25000)

try:
    deploy_origin = (
        f"from AWS Batch job `{environ['AWS_BATCH_JOB_ID']}`"
        if environ.get("AWS_BATCH_JOB_ID") else
        f"by the hands of {getuser()}@{getfqdn()}"
    )
except:
    # getuser() and getfqdn() may not always succeed, and this catch-all except
    # means that the Snakefile won't crash.
    deploy_origin = "by an unknown identity"

rule upload_region:
    input:
        auspice_json = "auspice/ncov_{build_name}.json",
        tree_nwk = "results/{build_name}/tree.nwk"
    output:
        temp(touch("upload_{build_name}"))
    params:
        auspice_json_s3_dest_url = lambda wildcards: f"{config['s3_staging_url']}/ncov_{wildcards.build_name}.json",
        tree_nwk_s3_dest_url = lambda wildcards: f"{config['s3_staging_url']}/tree_{wildcards.build_name}.nwk",
    conda: config["conda_environment"]
    shell:
        """
        aws s3 cp {input.auspice_json:q} {params.auspice_json_s3_dest_url:q}
        aws s3 cp {input.tree_nwk:q} {params.tree_nwk_s3_dest_url:q}
        """

rule upload_all:
    input:
        all_regions = expand("upload_{build_name}", build_name=BUILD_NAMES)
    params:
        slack_message = lambda wildcards: f":rotating_light: <!channel> Uploaded results for run {deploy_origin} to {config['s3_staging_url']}"
    conda: config["conda_environment"]
    shell:
        """
        if [[ -n "$SLACK_TOKEN" && -n "$SLACK_CHANNEL" ]]; then
            curl https://slack.com/api/chat.postMessage \
                --header "Authorization: Bearer $SLACK_TOKEN" \
                --form-string channel="$SLACK_CHANNEL" \
                --form-string text={params.slack_message:q} \
                --fail --silent --show-error \
                --include
        fi
        if [[ -n "$GH_USERNAME" ]]; then
                curl -fsS -u "$GH_USERNAME:$GH_TOKEN" \
                    https://api.github.com/repos/czbiohub/ncov-ingest/dispatches \
                    -H 'Accept: application/vnd.github.v3+json' \
                    -H 'Content-Type: application/json' \
                    -d '{{"event_type":"sync_to_covidtracker"}}'
        fi
        """
