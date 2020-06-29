rule upload_region:
    input:
        auspice_json = "auspice/ncov_{build_name}.json"
    output:
        temp(touch("upload_{build_name}"))
    params:
        s3_dest_url = lambda wildcards: f"{config['s3_staging_url']}/ncov_{wildcards.build_name}.json",
    conda: config["conda_environment"]
    shell:
        """
        aws s3 cp {input.auspice_json:q} {params.s3_dest_url:q}
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
        """
