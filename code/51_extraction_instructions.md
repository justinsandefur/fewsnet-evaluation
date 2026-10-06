# Extraction instructions: FEWS NET narrative reports

You are turning one FEWS NET report into structured data. Record only what the report says. Do not use anything you know about what happened later in this country: you may know how this crisis turned out, and that knowledge must not enter the data. If the report does not state something, leave it null or the list empty. Do not infer phases or numbers that are not written.

Input: one text file, `input/reports/text/<name>.txt` (country, report type and month are in the name). Output: one JSON file, `input/reports/extracted/<name>.json`, matching the schema below. Write valid JSON only (no comments).

## Schema

```json
{
  "name": "<file name without .txt>",
  "period_covered": "e.g. 'October 2013 - March 2014' as written, or null",
  "national": {
    "famine_risk_mentioned": true/false,          // Famine (IPC Phase 5) or 'risk of Famine' raised for any area
    "worst_case_described": true/false,           // an explicit worst-case / alternative scenario
    "worst_case_text": "<= 40 words, or null",
    "aid_assumption": "assumed_continued | assumed_scaled_up | assumed_reduced | pipeline_break_expected | not_stated",
    "aid_assumption_text": "<= 40 words quoting or paraphrasing the assistance assumption, or null",
    "people_in_need_crisis_plus": number or null, // people in Phase 3+ (or 'in need of assistance') stated nationally
    "headline_direction": "deteriorate | improve | stable | mixed | not_stated",
    "aid_assumption_changes": "<= 30 words if the assistance assumption differs across sub-periods or regions, else null",
    "people_stressed": number or null,            // people in Phase 2 stated nationally
    "upside_scenario_text": "<= 30 words on any better-than-expected scenario, or null",
    "rain_forecast": "above | average | below | mixed | not_stated",  // forecast for the next rainy season, as stated
    "season_status_text": "<= 25 words on whether the current/next season is late, failed, on time, or null"
  },
  "areas": [                                      // one entry per sub-national area the report discusses with a phase or direction
    {
      "location": "as written, e.g. 'Bay Agropastoral livelihood zone' or 'North Darfur'",
      "admin1": "region/state if identifiable from the text, else null",
      "admin2": "zone/district/locality if stated, else null",
      "livelihood_zone": "if stated, else null",
      "population_group": "residents | IDPs | refugees | pastoralists | urban poor | other | null",
      "current_phase": 1-5 or null,               // phase stated for now
      "projected_phase": 1-5 or null,             // most likely phase for the FIRST projection sub-period (near term)
      "projected_period": "as written or null",
      "projected_phase_2": 1-5 or null,           // most likely phase for a SECOND, later sub-period if the report gives one
      "projected_period_2": "as written or null",
      "aid_flag_or_held_back": true/false,        // text says assistance is keeping outcomes at least one phase better ('!' or equivalent)
      "worst_case_phase": 1-5 or null,            // phase in an explicit worst case / 'could reach' / 'risk of'
      "direction": "deteriorate | improve | stable | mixed | not_stated",
      "nutrition_class": "as written, e.g. 'Critical', 'Very Critical', 'IPC AMN Phase 4', or null",
      "price_change_pct": number or null,         // staple price change stated for this area (vs. last year or 5-yr average)
      "price_change_basis": "yoy | five_year_avg | other | null",
      "terms_of_trade_text": "<= 20 words or null",
      "people_in_need": number or null,           // people in need / Phase 3+ stated for this area
      "drivers": [ "rain_deficit | flood | harvest_poor | harvest_good | prices_high | prices_falling | currency | livestock | conflict | displacement | disease_outbreak | access_constraint | aid_reduction | aid_scaleup | trade_border | macro | other" ],
      "aid_status": "present | scaled_up | reduced_or_ending | pipeline_break_expected | access_blocked | absent | not_stated",
      "aid_coverage_pct_of_need": number or null, // e.g. 'reaching 35 percent of need' -> 35
      "uncertainty_language": true/false          // 'uncertain', 'limited information', 'could not be verified', etc. about this area
    }
  ],
  "surveys": [                                    // every nutrition, mortality or food security survey RESULT reported
    {
      "location": "as written",
      "admin1": "or null",
      "admin2": "or null",
      "population_group": "residents | IDPs | refugees | other | null",
      "survey_type": "SMART | SENS | mortality | FSNAU_seasonal | MUAC_screening | admissions | mVAM_phone | household_FS | other",
      "fieldwork": "month-year or as written, or null",
      "gam_pct": number or null,                  // global acute malnutrition, weight-for-height
      "sam_pct": number or null,
      "gam_muac_pct": number or null,
      "cdr": number or null,                      // crude death rate per 10,000 per day
      "u5dr": number or null,                     // under-five death rate per 10,000 per day
      "fcs_poor_pct": number or null,             // food consumption score 'poor', percent of households
      "other": "<= 20 words or null",
      "planned_not_done": true/false              // true if the survey is only planned / pending, no result
    }
  ],
  "data_sources_cited": [ "remote_sensing_rain | remote_sensing_vegetation | market_prices_fewsnet | market_prices_wfp | market_prices_other | smart_nutrition | mortality_survey | household_survey | phone_survey | key_informants | field_visit | joint_assessment_ipc | humanitarian_distribution_data | displacement_tracking | conflict_data | admissions_data | livestock_data | crop_assessment | trade_flows | other" ],
  "data_gaps": [                                  // explicit statements that information is missing, old, limited, or that access prevented collection
    {
      "location": "as written, or 'national'",
      "admin1": "or null",
      "what": "nutrition | mortality | prices | food_consumption | crop_production | assistance | displacement | access | general",
      "text": "<= 30 words"
    }
  ],
  "remote_monitoring": true/false                 // report says FEWS NET has no field presence / remote monitoring
}
```

## Rules

- Phases: map words to numbers. Minimal 1, Stressed 2, Crisis 3, Emergency 4, Famine/Catastrophe 5. "Crisis (IPC Phase 3) or worse" -> 3. "Crisis and Emergency" for one area -> record the higher phase, 4, only if the text clearly assigns Emergency to that area; otherwise 3.
- "Phase 3!" or "would be at least one phase worse without humanitarian assistance" -> `aid_flag_or_held_back: true`.
- Also include areas mentioned only with drivers or a direction and no phase; leave phases null.
- `admin1`/`admin2` may list several names separated by semicolons. Keep parent and child areas (e.g. a region and a district within it) as separate entries.
- One entry per distinct area per report. If the report gives several statements about the same area, merge them; prefer the most specific phase statement.
- National-only statements go in `national`, not `areas`.
- Surveys: record results only. If the report says a survey is planned, add it with `planned_not_done: true` and null results. Include refugee camp and IDP surveys.
- Data gaps: only explicit statements. Do not record a gap just because a source is not mentioned.
- Keep text fields short. The JSON for a long outlook should rarely exceed 25 area entries.
