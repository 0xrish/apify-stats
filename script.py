import json
import sys
from datetime import datetime

# =========================
# CONFIG
# =========================
INPUT_FILE = "./actors.json"
OUTPUT_JS_FILE = "./data.js" # Output as JS variable for easy local HTML loading

# User Reference: 303 Revenue -> 293 Profit
# Profit Margin = 293 / 303 ~= 0.96699
PROFIT_MARGIN = 293.0 / 303.0 

AVG_RESULTS_PER_RUN = 100
# Default pricing assumptions if missing
DEFAULT_PRICE_PER_EVENT = 0.005 
DEFAULT_PRICE_PER_MONTH = 49.0

# =========================
# UTILS
# =========================
def get_tiered_price(tiered_pricing):
    # Order of preference
    for tier in ["Free", "FREE", "BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND"]:
        if tier in tiered_pricing:
            return tiered_pricing[tier].get("tieredEventPriceUsd", 0)
    # Fallback
    if tiered_pricing:
        return list(tiered_pricing.values())[0].get("tieredEventPriceUsd", 0)
    return 0

def calculate_revenue_profit(actor):
    pricing = actor.get("currentPricingInfo", {})
    stats = actor.get("stats", {})
    model = pricing.get("pricingModel")

    # Metrics
    runs = stats.get("publicActorRunStats30Days", {}).get("SUCCEEDED", 0)
    users_30d = stats.get("totalUsers30Days", 0)
    
    gross_revenue = 0.0

    if model == "PAY_PER_EVENT":
        if "pricingPerEvent" in pricing:
            events = pricing["pricingPerEvent"].get("actorChargeEvents", {})
            
            # Base start price
            start_price = 0
            if "actor-start" in events:
                start_price = get_tiered_price(events["actor-start"].get("eventTieredPricingUsd", {}))
            
            # Recurring event price (max of recurring events)
            result_price = 0
            for key, event in events.items():
                if key != "actor-start" and not event.get("isOneTimeEvent", False):
                    p = get_tiered_price(event.get("eventTieredPricingUsd", {}))
                    if p > result_price:
                        result_price = p
            
            # Est Revenue = Runs * (Start + (Avg_Results * Item_Price))
            gross_revenue = runs * (start_price + (AVG_RESULTS_PER_RUN * result_price))
        else:
            # Fallback for Pay Per Event without detailed schema
            gross_revenue = runs * (AVG_RESULTS_PER_RUN * 0.002) # approx

    elif model == "FLAT_PRICE_PER_MONTH":
        price = pricing.get("pricePerUnitUsd", DEFAULT_PRICE_PER_MONTH)
        gross_revenue = users_30d * price

    elif model == "PRICE_PER_DATASET_ITEM":
        price = pricing.get("pricePerUnitUsd", 0.005)
        gross_revenue = runs * AVG_RESULTS_PER_RUN * price
    
    elif model == "FREE":
        gross_revenue = 0.0

    profit = gross_revenue * PROFIT_MARGIN

    return round(gross_revenue, 2), round(profit, 2)

def calculate_growth(stats):
    u7 = stats.get("totalUsers7Days", 0)
    u30 = stats.get("totalUsers30Days", 0)
    u90 = stats.get("totalUsers90Days", 0)
    
    # Growth Rate (Last 30 days vs previous period approx)
    # Prev 30 estimate = (90 - 30) / 2
    prev_30 = (u90 - u30) / 2
    rate = 0.0
    if prev_30 > 0:
        rate = ((u30 - prev_30) / prev_30) * 100
    
    return {
        "users_7d": u7,
        "users_30d": u30,
        "users_90d": u90,
        "growth_rate": round(rate, 1)
    }

def main():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            actors = json.load(f)
    except Exception as e:
        print(f"Error loading {INPUT_FILE}: {e}")
        return

    processed_data = []

    for actor in actors:
        stats = actor.get("stats", {})
        pricing = actor.get("currentPricingInfo", {})
        
        revenue, profit = calculate_revenue_profit(actor)
        growth = calculate_growth(stats)
        
        # Summarize Pricing (DSA: simplifying complex nested data for UI)
        price_summary = "Free"
        model = pricing.get("pricingModel", "FREE")
        if model == "PAY_PER_EVENT":
            events = pricing.get("pricingPerEvent", {}).get("actorChargeEvents", {})
            if "actor-start" in events:
                p = get_tiered_price(events["actor-start"].get("eventTieredPricingUsd", {}))
                price_summary = f"${p}/start"
            elif events:
                # Get first recurring event price
                first_event = next(iter(events.values()))
                p = get_tiered_price(first_event.get("eventTieredPricingUsd", {}))
                price_summary = f"${p}/event"
        elif model == "FLAT_PRICE_PER_MONTH":
            price_summary = f"${pricing.get('pricePerUnitUsd', 0)}/mo"
        elif model == "PRICE_PER_DATASET_ITEM":
            price_summary = f"${pricing.get('pricePerUnitUsd', 0)}/item"

        # Start with all original fields
        item = actor.copy()
        
        # Inject our calculated metrics and flattened metadata
        item.update({
            "pricingModel": model,
            "priceSummary": price_summary,
            "userFullName": actor.get("userFullName", "Unknown"),
            
            # Stats (normalized names for UI consistency)
            "runs_30d": stats.get("publicActorRunStats30Days", {}).get("TOTAL", 0),
            "users_7d": growth["users_7d"],
            "users_30d": growth["users_30d"],
            "users_90d": growth["users_90d"],
            "growth_rate": growth["growth_rate"],
            
            # Financials
            "estimated_revenue": revenue,
            "estimated_profit": profit,
            
            # Social shortcuts
            "rating": stats.get("actorReviewRating", 0),
            "reviews": stats.get("actorReviewCount", 0)
        })
        
        processed_data.append(item)

    # =========================
    # NORMALIZATION
    # =========================
    # User Intel: Apify pays ~$500k/month total profit to developers.
    
    TARGET_TOTAL_PROFIT = 500000.0
    
    total_raw_profit = sum(item["estimated_profit"] for item in processed_data)
    
    if total_raw_profit > 0:
        scaling_factor = TARGET_TOTAL_PROFIT / total_raw_profit
    else:
        scaling_factor = 1.0

    print(f"Calibrating estimates... Raw Total: ${total_raw_profit:,.2f} -> Target: ${TARGET_TOTAL_PROFIT:,.2f}")
    print(f"Scaling Factor: {scaling_factor}")

    for item in processed_data:
        # Apply scaling
        item["estimated_revenue"] = round(item["estimated_revenue"] * scaling_factor, 2)
        item["estimated_profit"] = round(item["estimated_profit"] * scaling_factor, 2)

    # Re-sort after scaling (order shouldn't change, but good practice)
    processed_data.sort(key=lambda x: x["estimated_profit"], reverse=True)

    # =========================
    # REPORTS
    # =========================

    with open("report.md", "w", encoding="utf-8") as f:
        # 1. Top Revenue
        f.write("-" * 60 + "\n")
        f.write("TOP 10 REVENUE GENERATORS (Calibrated to ~$500k Mkt Cap)\n")
        f.write("-" * 60 + "\n")
        f.write(f"{'Name':<40} | {'Revenue':<12} | {'Profit':<12} | {'Users':<8}\n")
        
        for a in processed_data[:10]:
            f.write(f"{a['title'][:38]:<40} | ${a['estimated_revenue']:<11,.2f} | ${a['estimated_profit']:<11,.2f} | {a['users_30d']:<8}\n")

        # 2. Fastest Growing (Velocity)
        f.write("\n" + "-" * 60 + "\n")
        f.write("TOP 10 FASTEST GROWING (Users Last 7 Days)\n")
        f.write("-" * 60 + "\n")
        f.write(f"{'Name':<40} | {'Users (7d)':<12} | {'Growth %':<10} | {'Est Profit':<10}\n")
        
        # Sort by 7d growth
        top_growth = sorted(processed_data, key=lambda x: x["users_7d"], reverse=True)
        for a in top_growth[:10]:
             f.write(f"{a['title'][:38]:<40} | {a['users_7d']:<12} | {a['growth_rate']:<9.1f}% | ${a['estimated_profit']:.0f}\n")

        # 3. High Users, Low Revenue
        f.write("\n" + "-" * 60 + "\n")
        f.write("HIGH DEMAND / LOW REVENUE (Opportunities)\n")
        f.write("-" * 60 + "\n")
        
        # Sort by users
        top_users = sorted(processed_data, key=lambda x: x["users_30d"], reverse=True)
        count = 0
        for a in top_users:
            if a["users_30d"] > 500 and a["estimated_profit"] < 100: # adjusted thresholds
                f.write(f"{a['title'][:40]:<40} | Users: {a['users_30d']:<6} | Profit: ${a['estimated_profit']:.2f}\n")
                count += 1
                if count >= 10: break
        
        # 4. Niche Analysis
        f.write("\n" + "-" * 60 + "\n")
        f.write("CATEGORY ANALYSIS (Niche Finding)\n")
        f.write("-" * 60 + "\n")
        categories = {}
        for a in processed_data:
            for cat in a["categories"]:
                if cat not in categories:
                    categories[cat] = {"profit": 0, "users": 0, "count": 0}
                categories[cat]["profit"] += a["estimated_profit"]
                categories[cat]["users"] += a["users_30d"]
                categories[cat]["count"] += 1
        
        cat_list = []
        for k, v in categories.items():
            if v["count"] > 0:
                avg_profit = v["profit"] / v["count"]
                avg_users = v["users"] / v["count"]
                cat_list.append({"name": k, "avg_profit": avg_profit, "avg_users": avg_users, "competition": v["count"]})
        
        f.write(f"{'Category':<25} | {'Avg Profit':<10} | {'Avg Users':<10} | {'Count':<10}\n")
        cat_list.sort(key=lambda x: x["avg_profit"], reverse=True)
        for c in cat_list[:10]:
             f.write(f"{c['name']:<25} | ${c['avg_profit']:<9.0f} | {c['avg_users']:<10.0f} | {c['competition']:<10}\n")


    # Output to data.js
    js_content = f"window.ACTOR_DATA = {json.dumps(processed_data, indent=2)};"
    
    with open(OUTPUT_JS_FILE, "w", encoding="utf-8") as f:
        f.write(js_content)
    
    print(f"Successfully processed {len(processed_data)} actors.")
    print(f"Data saved to {OUTPUT_JS_FILE}")

if __name__ == "__main__":
    main()

