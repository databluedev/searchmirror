from datetime import datetime, timedelta
# from serp.custom_serializer.widget_serializers import *
from serp.e_comm_metrics.e_com_serializers import *
from operator import itemgetter
from django.utils import timezone

def is_branded_keyword(keyword, branded_keywords):
    for each_branded_keyword in branded_keywords:
        if each_branded_keyword in keyword:
            return True
    return False


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


def reverse_sign(f):
    return -f


def reverse_percentage(percentage_str):

    percentage_str = str(percentage_str)

    # Remove the percentage sign and convert to a float
    number = float(percentage_str.strip("%"))

    if number == 0.0:
        return percentage_str

    # Reverse the sign
    reversed_number = -number

    # Convert back to string and add percentage sign
    reversed_percentage_str = f"{reversed_number}%"

    return reversed_percentage_str


# Format this date
def gsc_date_formatter(original_date, interval):
    try:
        # print(original_date)

        if interval == "M":

            # Adjust to match the expected format
            # original_date = original_date.replace(" ", "T") + ".000000Z"

            # Parse using the expected format
            dt_object = datetime.strptime(original_date, "%Y-%m-%d %H:%M:%S%z")

            # Format to the desired format
            formatted_date = dt_object.strftime("%b %y")
        else:

            # original_date = original_date.replace(" ", "T") + ".000000Z"

            # Convert to datetime object
            dt_object = datetime.strptime(original_date, "%Y-%m-%d %H:%M:%S%z")

            # Format to the desired format
            formatted_date = dt_object.strftime("%d %b")

        return formatted_date
    except Exception as e:
        print(e)
        return ""


# Function to reorder fields in each record
def reorder_brand_data(data, duration):
    reordered_data = []
    if duration == "weekly":
        for record in data:
            reordered_record = {
                "Week": record["Duration"],
                "Clicks": record["Clicks"],
                "MOM Change": str(record["MOM Change"]) + "%",
                "Brand Click Share": str(record["Brand Click Share"]) + "%",
                "Impressions": record["Impressions"],
                "CTR": str(round(record["CTR"], 1)) + "%",
                "Avg.Position": round(record["Avg.Position"], 1),
                # "brand_queries": round(record["brand_queries"], 2),
                # "brand_pos": round(record["brand_pos"], 2),
            }
            reordered_data.append(reordered_record)
    else:
        for record in data:
            reordered_record = {
                "Month": record["Duration"],
                "Clicks": record["Clicks"],
                "MOM Change": str(record["MOM Change"]) + "%",
                "Brand Click Share": str(record["Brand Click Share"]) + "%",
                "Impressions": record["Impressions"],
                "CTR": str(round(record["CTR"], 1)) + "%",
                "Avg.Position": round(record["Avg.Position"], 1),
            }
            reordered_data.append(reordered_record)

    return reordered_data


# Function to reorder fields in each record
def reorder_overview_data(data, duration):
    reordered_data = []
    for record in data:
        reordered_record = {}
        if duration == "weekly":
            reordered_record["Week"] = record["duration"]
        else:
            reordered_record["Month"] = record["duration"]

        reordered_record["Total Clicks"] = record["overview"]["clicks"]
        reordered_record["Total Impressions"] = record["overview"]["impressions"]
        reordered_record["CTR"] = str(round(record["overview"]["ctr"], 1)) + "%"
        reordered_record["Avg.Position"] = round(record["overview"]["position"], 1)

        reordered_data.append(reordered_record)

    return reordered_data


# Function to reorder fields in each record
def reorder_non_brand_data(data, duration):
    reordered_data = []
    if duration == "weekly":
        for record in data:
            reordered_record = {
                "Week": record["Duration"],
                "Clicks": record["Clicks"],
                "MOM Change": str(record["MOM Change"]) + "%",
                "Non-Brand Click Share": str(record["Non-Brand Click Share"]) + "%",
                "Impressions": record["Impressions"],
                "CTR": str(round(record["CTR"], 1)) + "%",
                "Avg.Position": round(record["Avg.Position"], 1),
                # "non_brand_queries": round(record["non_brand_queries"], 2),
                # "non_brand_pos": round(record["non_brand_pos"], 2),
            }
            reordered_data.append(reordered_record)
    else:
        for record in data:
            reordered_record = {
                "Month": record["Duration"],
                "Clicks": record["Clicks"],
                "MOM Change": str(record["MOM Change"]) + "%",
                "Non-Brand Click Share": str(record["Non-Brand Click Share"]) + "%",
                "Impressions": record["Impressions"],
                "CTR": str(round(record["CTR"], 1)) + "%",
                "Avg.Position": round(record["Avg.Position"], 1),
                # "non_brand_queries": round(record["non_brand_queries"], 2),
                # "non_brand_pos": round(record["non_brand_pos"], 2),
            }
            reordered_data.append(reordered_record)

    return reordered_data


def format_overview(data, type, timespan):
    clicks_overview = ""
    clicks_pct_diff = 0
    
    for i in range(1, len(data)):
        current = data[i]
        previous = data[i - 1]

        # Calculate number difference for clicks
        clicks_diff = current["Clicks"] - previous["Clicks"]

        # Calculate percentage difference for clicks
        clicks_pct_diff = round((clicks_diff / previous["Clicks"]) * 100, 2) if previous["Clicks"] != 0 else 0

        # Update 'MOM Change' with percentage difference of clicks
        current["MOM Change"] = clicks_pct_diff

        clicks_change = "raised" if clicks_pct_diff > 0 else "dropped"

    if type == "brand":
        if clicks_pct_diff:
            clicks_overview = f"The Brand clicks have {clicks_change} by {clicks_pct_diff}% from keywords"

        return reorder_brand_data(data, timespan), clicks_overview
    else:
        if clicks_pct_diff:
            clicks_overview = f"The Non-Brand clicks have {clicks_change} by {clicks_pct_diff}% from keywords"

        return reorder_non_brand_data(data, timespan), clicks_overview


def gsc_report(type, userId, grpId, branded_queries, timespan, filter_options):
    try:
        key_observations = []

        isDesc = True if filter_options["order_by"] == "desc" else False

        # Get the start of the current week
        three_days_ago = timezone.now() - timedelta(days=4)

        if timespan == "weekly":
            gsc_data = GSCWeeklyQuery.objects.filter(fk_group_id=int(grpId), fk_user_id=userId, week_end_date__lte=three_days_ago).values("id", "queries", "pages", "overview", "week_start_date", "week_end_date", "created_date").order_by("-week_start_date")[: filter_options["duration_limit"]]
            gsc_data = sorted(gsc_data, key=itemgetter("week_start_date"), reverse=isDesc)
            serialized_gsc_data = GSCWeeklyQDataSerializer(gsc_data, many=True).data
        else:
            gsc_data = (
                GSCMonthlyQuery.objects.filter(
                    fk_group_id=int(grpId),
                    fk_user_id=userId,
                )
                .values("id", "queries", "pages", "overview", "month_start_date", "month_end_date", "created_date")
                .order_by("-month_start_date")[: filter_options["duration_limit"]]
            )
            gsc_data = sorted(gsc_data, key=itemgetter("month_start_date"), reverse=isDesc)
            serialized_gsc_data = GSCMonthlyQDataSerializer(gsc_data, many=True).data

        if not serialized_gsc_data:
            return [], [], [], [], [], [], [], []

        gsc_query_data = []
        gsc_overview_query_data = []

        for each_gsc_data in serialized_gsc_data:
            each_record = {}
            if timespan == "weekly":
                each_record["duration"] = gsc_date_formatter(str(each_gsc_data["week_start_date"]), "W") + "-" + gsc_date_formatter(str(each_gsc_data["week_end_date"]), "W")
            else:
                each_record["duration"] = gsc_date_formatter(str(each_gsc_data["month_start_date"]), "M")

            # print(each_record)
            each_record["queries"] = each_gsc_data["queries"] if type == "queries" else each_gsc_data["pages"]
            gsc_query_data.append(each_record)

            overview_record = {}
            overview_record["duration"] = each_record["duration"]
            overview_record["overview"] = each_gsc_data["overview"]
            gsc_overview_query_data.append(overview_record)

        overall_data = []
        overall_brand_data = []
        overall_non_brand_data = []

        gsc_query_clicks = {}
        gsc_query_impressions = {}
        gsc_query_position = {}
        gsc_query_ctr = {}

        time_ranges = [each_query_data["duration"] for each_query_data in gsc_query_data]
        for each_query_data in gsc_query_data:

            # OVERVIEW DATA
            kw_clicks = 0
            kw_impressions = 0

            kw_pos = 0

            brand_clicks = 0
            brand_impresions = 0
            brand_pos = 0
            brand_queries = 0

            non_brand_clicks = 0
            non_brand_impressions = 0
            non_brand_pos = 0
            non_brand_queries = 0

            for query_data in each_query_data.get("queries", []):
                query = query_data["query"]
                clicks = query_data.get("clicks", "-")
                impressions = query_data.get("impressions", "-")
                ctr = query_data.get("ctr", "-")
                pos = query_data.get("position", "-")

                if query not in gsc_query_clicks:
                    gsc_query_clicks[query] = {}
                    gsc_query_impressions[query] = {}
                    gsc_query_position[query] = {}
                    gsc_query_ctr[query] = {}

                kw_clicks += clicks
                kw_impressions += impressions
                kw_pos += pos

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    brand_clicks += clicks
                    brand_impresions += impressions
                    if pos <= 100:
                        brand_pos += pos
                        brand_queries += 1
                else:
                    non_brand_clicks += clicks
                    non_brand_impressions += impressions
                    if pos <= 100:
                        non_brand_pos += pos
                        non_brand_queries += 1

                gsc_query_clicks[query][each_query_data["duration"]] = {"clicks": clicks}
                gsc_query_impressions[query][each_query_data["duration"]] = {"impressions": impressions}
                gsc_query_position[query][each_query_data["duration"]] = {"position": pos}
                gsc_query_ctr[query][each_query_data["duration"]] = {"ctr": ctr}

            overall_data.append(
                {
                    "Duration": each_query_data["duration"],
                    "Total Clicks": kw_clicks,
                    "Total Impressions": kw_impressions,
                    "CTR": round((kw_clicks / kw_impressions) * 100, 2) if kw_impressions > 0 else 0,
                }
            )
            if type not in ["pages"]:
                overall_brand_data.append(
                    {
                        "Duration": each_query_data["duration"],
                        "Clicks": brand_clicks,
                        "Impressions": brand_impresions,
                        "CTR": round((brand_clicks / brand_impresions) * 100, 2) if brand_impresions > 0 else 0,
                        "Avg.Position": round((brand_pos / brand_queries), 2) if brand_queries > 0 else 0,
                        "MOM Change": 0,
                        "Brand Click Share": round((brand_clicks / kw_clicks) * 100, 2) if kw_clicks > 0 else 0,
                        # "brand_pos": brand_pos,
                        # "brand_queries": brand_queries,
                    }
                )

            overall_non_brand_data.append(
                {
                    "Duration": each_query_data["duration"],
                    "Clicks": non_brand_clicks,
                    "Impressions": non_brand_impressions,
                    "CTR": round((non_brand_clicks / non_brand_impressions) * 100, 2) if non_brand_impressions > 0 else 0,
                    "Avg.Position": round((non_brand_pos / non_brand_queries), 2) if non_brand_queries > 0 else 0,
                    "MOM Change": 0,
                    "Non-Brand Click Share": round((non_brand_clicks / kw_clicks) * 100, 2) if kw_clicks > 0 else 0,
                    # "non_brand_pos": non_brand_pos,
                    # "non_brand_queries": non_brand_queries,
                }
            )

        overall_branded_data = {}
        overall_non_branded_data = {}
        branded_id = 1
        non_branded_id = 1
        for query, query_data in gsc_query_clicks.items():
            query_entry = {}
            query_clicks = 0
            clicks_change = 0
            limit_click_sort = 0

            if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                query_entry["Sr No"] = branded_id
                branded_id += 1
            else:
                query_entry["Sr No"] = non_branded_id
                non_branded_id += 1

            for time in time_ranges:
                time_info = query_data.get(time, {"clicks": "-"})
                if filter_options["order_by"] == "asc" or filter_options["order_by"] == "desc" and limit_click_sort < 2:
                    if time_info["clicks"] not in ["-"]:
                        clicks_per_change = calculate_percentage_difference(query_clicks, time_info["clicks"])
                        clicks_change = time_info["clicks"] - query_clicks
                        query_clicks = time_info["clicks"]
                    else:
                        clicks_per_change = "0%"
                        clicks_change = 0
                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    query_entry["Type"] = "Brand"
                    query_entry["Top Brand Queries"] = query
                elif type not in ["pages"] and not is_branded_keyword(query, branded_queries):
                    query_entry["Type"] = "Non-Brand"
                    query_entry["Top Non-Brand Queries"] = query
                else:
                    query_entry["Pages"] = query

                if "clicks" in filter_options["metrics"]:
                    query_entry[time + " Clicks"] = time_info["clicks"]

                limit_click_sort = limit_click_sort + 1

            if "clicks" in filter_options["metrics"]:
                clicks_change_text = "Click Change" if timespan == "weekly" else "MOM Change\n(Clicks)"
                clicks_change_per_text = "Click Change (%)" if timespan == "weekly" else "MOM % Change\n(Clicks)"
                if "number" in filter_options["change_units"]:
                    query_entry[clicks_change_text] = reverse_sign(clicks_change) if filter_options["order_by"] == "desc" else clicks_change
                if "percentage" in filter_options["change_units"]:
                    query_entry[clicks_change_per_text] = reverse_percentage(clicks_per_change) if filter_options["order_by"] == "desc" else clicks_per_change

            if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                overall_branded_data[query] = query_entry
            else:
                overall_non_branded_data[query] = query_entry

        if "impressions" in filter_options["metrics"]:
            impressions_change_text = "Impressions Change" if timespan == "weekly" else "MOM Change\n(Impressions)"
            impressions_change_per_text = "Impressions Change (%)" if timespan == "weekly" else "MOM % Change\n(Impressions)"
            for query, query_data in gsc_query_impressions.items():
                impressions_change = 0
                impressions_per_change = 0
                query_impressions = 0
                limit_impression_sort = 0
                for time in time_ranges:

                    time_info = query_data.get(time, {"impressions": "-"})

                    if filter_options["order_by"] == "asc" or filter_options["order_by"] == "desc" and limit_impression_sort < 2:
                        if time_info["impressions"] not in ["-"]:
                            impressions_per_change = calculate_percentage_difference(query_impressions, time_info["impressions"])
                            impressions_change = time_info["impressions"] - query_impressions
                            query_impressions = time_info["impressions"]
                        else:
                            impressions_per_change = "0%"
                            impressions_change = 0

                    if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                        overall_branded_data[query][time + " Impressions"] = time_info["impressions"]
                    else:
                        overall_non_branded_data[query][time + " Impressions"] = time_info["impressions"]

                    limit_impression_sort = limit_impression_sort + 1

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    if "number" in filter_options["change_units"]:
                        overall_branded_data[query][impressions_change_text] = reverse_sign(impressions_change) if filter_options["order_by"] == "desc" else impressions_change
                    if "percentage" in filter_options["change_units"]:
                        overall_branded_data[query][impressions_change_per_text] = reverse_percentage(impressions_per_change) if filter_options["order_by"] == "desc" else impressions_per_change
                else:
                    if "number" in filter_options["change_units"]:
                        overall_non_branded_data[query][impressions_change_text] = reverse_sign(impressions_change) if filter_options["order_by"] == "desc" else impressions_change
                    if "percentage" in filter_options["change_units"]:
                        overall_non_branded_data[query][impressions_change_per_text] = reverse_percentage(impressions_per_change) if filter_options["order_by"] == "desc" else impressions_per_change

        if "position" in filter_options["metrics"]:
            position_change_text = "Position Change" if timespan == "weekly" else "MOM Change\n(Avg.Position)"
            position_change_per_text = "Position Change (%)" if timespan == "weekly" else "MOM % Change\n(Avg.Position)"
            for query, query_data in gsc_query_position.items():
                position_change = 0
                position_per_change = 0
                query_position = 0
                limit_position_sort = 0
                for time in time_ranges:

                    time_info = query_data.get(time, {"position": "-"})

                    if filter_options["order_by"] == "asc" or filter_options["order_by"] == "desc" and limit_position_sort < 2:
                        if time_info["position"] not in ["-"]:
                            position_per_change = calculate_percentage_difference(query_position, time_info["position"])
                            position_change = time_info["position"] - query_position
                            query_position = time_info["position"]
                        else:
                            position_per_change = "0%"
                            position_change = 0

                    if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                        overall_branded_data[query][time + " Position"] = time_info["position"]
                    else:
                        overall_non_branded_data[query][time + " Position"] = time_info["position"]

                    limit_position_sort = limit_position_sort + 1

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    if "number" in filter_options["change_units"]:
                        overall_branded_data[query][position_change_text] = reverse_sign(round(position_change)) if filter_options["order_by"] == "desc" else round(position_change)
                    if "percentage" in filter_options["change_units"]:
                        overall_branded_data[query][position_change_per_text] = reverse_percentage(position_per_change) if filter_options["order_by"] == "desc" else position_per_change
                else:
                    if "number" in filter_options["change_units"]:
                        overall_non_branded_data[query][position_change_text] = reverse_sign(round(position_change)) if filter_options["order_by"] == "desc" else round(position_change)
                    if "percentage" in filter_options["change_units"]:
                        overall_non_branded_data[query][position_change_per_text] = reverse_percentage(position_per_change) if filter_options["order_by"] == "desc" else position_per_change


        if "ctr" in filter_options["metrics"]:
            ctr_change_text = "CTR Change" if timespan == "weekly" else "MOM Change\n(CTR)"
            ctr_change_per_text = "CTR Change (%)" if timespan == "weekly" else "MOM % Change\n(CTR)"

            for query, query_data in gsc_query_ctr.items():
                ctr_change = 0
                ctr_per_change = 0
                query_ctr = 0
                limit_ctr_sort = 0
                for time in time_ranges:

                    if filter_options["order_by"] == "asc" or filter_options["order_by"] == "desc" and limit_ctr_sort < 2:
                        time_info = query_data.get(time, {"ctr": "-"})
                        if time_info["ctr"] not in ["-"]:
                            ctr_per_change = calculate_percentage_difference(query_ctr, time_info["ctr"])
                            ctr_change = time_info["ctr"] - query_ctr
                            query_ctr = time_info["ctr"]
                        else:
                            ctr_per_change = "0%"
                            ctr_change = 0

                    if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                        overall_branded_data[query][time + " ctr"] = time_info["ctr"]
                    else:
                        overall_non_branded_data[query][time + " ctr"] = time_info["ctr"]

                    limit_ctr_sort = limit_ctr_sort + 1

                if type not in ["pages"] and is_branded_keyword(query, branded_queries):
                    if "number" in filter_options["change_units"]:
                        overall_branded_data[query][ctr_change_text] = reverse_sign(round(ctr_change)) if filter_options["order_by"] == "desc" else round(ctr_change)
                    if "percentage" in filter_options["change_units"]:
                        overall_branded_data[query][ctr_change_per_text] = reverse_percentage(ctr_per_change) if filter_options["order_by"] == "desc" else ctr_per_change
                else:
                    if "number" in filter_options["change_units"]:
                        overall_non_branded_data[query][ctr_change_text] = reverse_sign(round(ctr_change)) if filter_options["order_by"] == "desc" else round(ctr_change)
                    if "percentage" in filter_options["change_units"]:
                        overall_non_branded_data[query][ctr_change_per_text] = reverse_percentage(ctr_per_change) if filter_options["order_by"] == "desc" else ctr_per_change

        search_overview_result = []

        if len(gsc_query_data) > 0:

            # Calculate and update the MOM Change for each month
            if overall_brand_data:
                overall_brand_data, change_overview = format_overview(overall_brand_data, "brand", timespan)
                if change_overview:
                    search_overview_result.append(change_overview)

            if overall_non_brand_data:
                overall_non_brand_data, change_overview = format_overview(overall_non_brand_data, "non_brand", timespan)
                if change_overview:
                    search_overview_result.append(change_overview)

            gsc_overview_query_data = reorder_overview_data(gsc_overview_query_data, timespan)

        return list(overall_branded_data.values()), list(overall_non_branded_data.values()), overall_data, overall_brand_data, overall_non_brand_data, search_overview_result, key_observations, gsc_overview_query_data

    except Exception as e:
        print(f'537 gsc_metrics {str(e)}')
        return [], [], [], [], [], [], [], []