from api.db.database import get_db
from api.v1.models.billing_plan import BillingPlan


db = next(get_db())

def load_billing_plans_in_db():
    free_plan = BillingPlan(
        id="free",
        plan_name="Free",
        price=0,
        access_limit=15,
        plan_interval='one-off',
        currency='USD',
        features=[
            'Access to tools',
            'Text to Video',
            'Image to Video',
            'Talking Avatar Generator',
            'Youtube Summarizer',
            'Podcast Summarizer',
            'Limited Processing',
            'Watermark on videos'
        ]
    )

    premium_monthly_plan = BillingPlan(
        id='premium_monthly',
        plan_name="Premium Monthly",
        price=4.99,
        plan_interval='monthly',
        access_limit=50,
        currency='USD',
        features=[
            'Access to tools',
            'Text to Video',
            'Image to Video',
            'Talking Avatar Generator',
            'Youtube Summarizer',
            'Podcast Summarizer',
            'Watermark free videos',
            'Early access to new features',
            'Early access to future tools'
        ]
    )

    premium_yearly_plan = BillingPlan(
        id='premium_yearly',
        plan_name="Premium Yearly",
        price=49.99,
        plan_interval='yearly',
        access_limit=75,
        currency='USD',
        features=[
            'Access to tools',
            'Text to Video',
            'Image to Video',
            'Talking Avatar Generator',
            'Youtube Summarizer',
            'Podcast Summarizer',
            'Watermark free videos',
            'Early access to new features',
            'Early access to future tools',
            'Save 15% compared to monthly'
        ]
    )
    
    plans = [free_plan, premium_monthly_plan, premium_yearly_plan]
    
    for i in plans:
        if not db.query(BillingPlan).filter(BillingPlan.id == i.id).first():
            db.query(BillingPlan).delete()
            db.commit()
            for plan in plans:
                db.add(plan)
                db.commit()
                db.refresh(plan)
            return True