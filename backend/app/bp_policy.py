"""Technical pending-review gate, NOT a clinical rule or a diagnosis.

No mixing of reading numbers; ambiguous/inconsistent sessions remain in the
warehouse/raw source but are excluded pending a documented scientific decision.
"""
import math
import pandas as pd

POLICY_VERSION='paired-reading-review-v1'

def assess_session(row,invalid_fields=()):
    reasons=[];pairs=[];partial=False
    for number in (1,2):
        a,b=row.get(f'sbp{number}'),row.get(f'dbp{number}')
        a=None if pd.isna(a) else a;b=None if pd.isna(b) else b
        if a is None and b is None:continue
        if a is None or b is None:partial=True;continue
        if not (math.isfinite(a) and math.isfinite(b) and 60<=a<=260 and 35<=b<=170):
            reasons.append('outside_existing_technical_bounds');continue
        if a<=b:reasons.append('sbp_not_above_dbp');continue
        pairs.append((float(a),float(b)))
    if partial:reasons.append('unpaired_component_pending_decision')
    if invalid_fields:reasons.append('invalid_source_reading')
    # Null derived values from an earlier ETL review are never reconstructed away.
    if pairs and not reasons and 'sbp_mean' in row and (pd.isna(row.get('sbp_mean')) or pd.isna(row.get('dbp_mean'))):
        reasons.append('stored_derived_missing_pending_review')
    ready=bool(pairs) and not reasons
    return dict(sbp_mean=sum(a for a,b in pairs)/len(pairs) if ready else None,
                dbp_mean=sum(b for a,b in pairs)/len(pairs) if ready else None,
                is_valid=ready,valid_pair_count=len(pairs),
                review_status='ready' if ready else 'pending_review' if reasons else 'incomplete',
                review_reasons=';'.join(sorted(set(reasons))))

def assessed_frame(frame):
    frame=frame.copy()
    columns=['sbp_mean','dbp_mean','is_valid','valid_pair_count','review_status','review_reasons']
    results=pd.DataFrame([assess_session(row) for row in frame.to_dict('records')],index=frame.index,columns=columns)
    for column in columns:frame[column]=results[column]
    frame['is_valid']=frame['is_valid'].astype(bool)
    return frame
