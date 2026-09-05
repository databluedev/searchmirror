from serp.models import *
# from serp.custom_serializer.widget_serializers import DomainTrackSerializer
from serp.e_comm_metrics.e_com_serializers import DomainTrackSerializer

def reverse_sign(f):
    return -f


def reverse_percentage(percentage_str):
    # Remove the percentage sign and convert to a float
    number = float(percentage_str.strip("%"))

    if number == 0.0:
        return percentage_str

    # Reverse the sign
    reversed_number = -number

    # Convert back to string and add percentage sign
    reversed_percentage_str = f"{reversed_number}%"

    return reversed_percentage_str

def calculate_percentage_difference(old_value, new_value):
    if old_value == 0:
        if new_value == 0:
            return "0%"
        else:
            return "100%"

    # Calculate the percentage difference
    percentage_difference = (new_value - old_value) / old_value * 100

    # Format the percentage difference with the plus or minus symbol and one decimal point
    formatted_percentage_difference = "{:+.1f}%".format(percentage_difference)

    return formatted_percentage_difference

def generate_monthly_metrics(monthly_data, metric_type, filter_options, metric_key, metric_name):
    monthly_metrics = {}
    metric_difference = 0
    percentage_diff = 0
    metric_difference = 0
    # if metric_type in ["da", "dr"]:
    #     monthly_metrics["Area"] = "Authority"
    # elif metric_type in ["backlinks", "ref_domains"]:
    #     monthly_metrics["Area"] = "Backlinks"
    # else:
    #     monthly_metrics["Area"] = "Website Usability"

    monthly_metrics["Key SEO Metrics"] = metric_name
    prev_value = 0
    for data in monthly_data:

        month, year = data["month"].split()
        month_abbr = month[:3].upper()
        year_abbr = year[2:]
        monthly_metrics[f"{month_abbr}'{year_abbr}"] = data[metric_key]

        if not data[metric_key] == "NA" and not prev_value == "NA" and not isinstance(data[metric_key], str):
            metric_difference = data[metric_key] - prev_value
            percentage_diff = calculate_percentage_difference(prev_value, data[metric_key])

        prev_value = data[metric_key]

    if "number" in filter_options["change_units"]:
        monthly_metrics["MOM Change"] = metric_difference if filter_options["order_by"] == "asc" else reverse_sign(metric_difference)
    if "percentage" in filter_options["change_units"]:
        monthly_metrics["MOM Change (%)"] = percentage_diff if filter_options["order_by"] == "asc" else reverse_percentage(percentage_diff)

    return monthly_metrics

def seo_metrics_sub(userId, grpId, filter_options):
    try:
        seo_metrics = list()
        metrics_data = DomainTracking.objects.filter(fk_group_id=int(grpId), fk_user_id=userId).values("da_metrics", "dr_metrics", "page_speed_metrics").first()
        serialized_metrics_data = DomainTrackSerializer(metrics_data, context={"order_by": filter_options["order_by"]}).data

        if len(serialized_metrics_data["da_metrics"]) == 0 and len(serialized_metrics_data["dr_metrics"]) == 0 and len(serialized_metrics_data['page_speed_metrics']):
            return []

        da_metrics = generate_monthly_metrics(serialized_metrics_data["da_metrics"][: filter_options["duration_limit"]], "da", filter_options, "value", "Domain Authority (MOZ)")
        seo_metrics.append(da_metrics)

        dr_metrics = generate_monthly_metrics(serialized_metrics_data["dr_metrics"][: filter_options["duration_limit"]], "dr", filter_options, "value", "Domain Rating (AHREFs)")
        seo_metrics.append(dr_metrics)

        backlinks_metrics = generate_monthly_metrics(serialized_metrics_data["dr_metrics"][: filter_options["duration_limit"]], "backlinks", filter_options, "backlinks", "Number of Backlinks (AHREFs)")
        seo_metrics.append(backlinks_metrics)

        ref_metrics = generate_monthly_metrics(serialized_metrics_data["dr_metrics"][: filter_options["duration_limit"]], "ref_domains", filter_options, "ref_domains", "Referring Domains (AHREFs)")
        seo_metrics.append(ref_metrics)

        if 'page_speed_metrics' in serialized_metrics_data:
            desktop_page_speed = generate_monthly_metrics(serialized_metrics_data["page_speed_metrics"][: filter_options["duration_limit"]], "desktop_speed", filter_options, "dsk_speed", "Desktop Speed")
            seo_metrics.append(desktop_page_speed)

        if 'page_speed_metrics' in serialized_metrics_data:
            mobile_page_speed = generate_monthly_metrics(serialized_metrics_data["page_speed_metrics"][: filter_options["duration_limit"]], "mobile_speed", filter_options, "mbl_speed", "Mobile Speed")
            seo_metrics.append(mobile_page_speed)

        if 'page_speed_metrics' in serialized_metrics_data:
            web_vitals = generate_monthly_metrics(serialized_metrics_data["page_speed_metrics"][: filter_options["duration_limit"]], "web_vitals_mbl", filter_options, "web_vitals_mbl", "Core web vital(Mobile)")
            seo_metrics.append(web_vitals)

        if 'page_speed_metrics' in serialized_metrics_data:
            page_metrics = generate_monthly_metrics(serialized_metrics_data["page_speed_metrics"][: filter_options["duration_limit"]], "mbl_friendliness", filter_options, "mbl_friendliness", "Mobile Friendliness")
            seo_metrics.append(page_metrics)

        return seo_metrics

    except Exception as e:
        print(str(e))
        print(e.args)
        return []