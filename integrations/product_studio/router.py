"""MN24 AI Product Studio: prompt-to-spec, UX planning and financial modelling.

This MVP is deterministic. It does not call an LLM, write arbitrary files,
execute generated code, deploy applications, or provide investment advice.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, model_validator

router = APIRouter(prefix="/studio", tags=["MN24 AI Product Studio"])

Platform = Literal["web", "android", "pwa"]


class ProductBrief(BaseModel):
    product_name: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=10, max_length=4000)
    target_users: str = Field(min_length=2, max_length=500)
    platforms: list[Platform] = Field(min_length=1, max_length=3)
    budget_usd: float = Field(default=100, gt=0, le=100)


class FinanceRequest(BaseModel):
    initial_investment: float = Field(gt=0, le=1_000_000_000)
    annual_cash_flows: list[float] = Field(min_length=1, max_length=10)
    discount_rate: float = Field(gt=0, le=1)
    terminal_growth_rate: float = Field(default=0, ge=0, lt=1)

    @model_validator(mode="after")
    def validate_growth_below_discount(self):
        if self.terminal_growth_rate >= self.discount_rate:
            raise ValueError("terminal_growth_rate must be lower than discount_rate")
        return self


@router.get("/status")
async def status() -> dict:
    return {
        "module": "MN24 AI Product Studio",
        "status": "IMPLEMENTADO",
        "execution_mode": "deterministic_mvp_no_external_llm",
        "features": {
            "lovable_inspired_app_builder": "SIMULADO",
            "vibe_coding_specification": "IMPLEMENTADO",
            "ux_ui_design_brief": "IMPLEMENTADO",
            "user_centered_design": "IMPLEMENTADO",
            "value_investing_calculator": "IMPLEMENTADO",
            "automated_test_and_deploy_pipeline": "PENDIENTE",
        },
        "safety": {
            "generated_code_execution": False,
            "automatic_deployment": False,
            "financial_advice": False,
        },
    }


@router.post("/plan")
async def create_product_plan(brief: ProductBrief) -> dict:
    """Turn a user brief into an editable product/UX/engineering blueprint."""
    platforms = list(dict.fromkeys(brief.platforms))
    return {
        "status": "IMPLEMENTADO",
        "generation_mode": "template_based_simulation",
        "brief": brief.model_dump(),
        "product_specification": {
            "problem_statement": brief.description,
            "primary_audience": brief.target_users,
            "success_metrics": [
                "task_completion_rate",
                "time_to_complete_primary_task",
                "weekly_active_users",
                "crash_free_sessions",
            ],
            "platforms": platforms,
            "budget_cap_usd": brief.budget_usd,
        },
        "ux_ui_studio": {
            "deliverables": ["responsive_wireframe", "design_tokens", "component_inventory", "accessibility_review"],
            "design_principles": ["mobile_first", "consistent_navigation", "WCAG_2_2_AA_target", "clear_feedback"],
        },
        "user_centered_design": {
            "research_tasks": ["interview_5_target_users", "map_top_3_user_journeys", "validate_problem_assumptions"],
            "usability_test": {"participants_target": 5, "tasks": ["onboarding", "complete_primary_task", "recover_from_error"]},
        },
        "vibe_coding": {
            "implementation_tasks": ["create_frontend_shell", "define_api_contracts", "add_persistence_after_review", "write_unit_and_e2e_tests"],
            "human_review_required": True,
            "generated_source_files": [],
            "note": "This endpoint creates a specification, not executable application code.",
        },
        "lovable_inspired_builder": {
            "preview": "blueprint_only",
            "code_generation": "PENDING",
            "visual_editor": "PENDING",
            "backend_scaffolding": "PENDING",
        },
        "testing_deployment": {
            "test_plan": ["unit", "api_contract", "accessibility", "browser_e2e", "android_device"],
            "deployment": "manual_only_pending_ci_and_release_signing",
        },
    }


@router.post("/finance/evaluate")
async def evaluate_project(payload: FinanceRequest) -> dict:
    """Illustrative discounted-cash-flow model; not a security valuation opinion."""
    rate = payload.discount_rate
    growth = payload.terminal_growth_rate
    cash_flows = payload.annual_cash_flows
    pv_cash_flows = [cf / ((1 + rate) ** year) for year, cf in enumerate(cash_flows, start=1)]
    terminal_value = cash_flows[-1] * (1 + growth) / (rate - growth)
    pv_terminal = terminal_value / ((1 + rate) ** len(cash_flows))
    intrinsic_value = sum(pv_cash_flows) + pv_terminal
    npv = intrinsic_value - payload.initial_investment
    margin_of_safety = (intrinsic_value - payload.initial_investment) / intrinsic_value if intrinsic_value > 0 else None
    simple_total_cash = sum(cash_flows)
    simple_roi = (simple_total_cash - payload.initial_investment) / payload.initial_investment
    return {
        "status": "IMPLEMENTADO",
        "model": "simplified_dcf_scenario",
        "currency": "USD",
        "initial_investment": round(payload.initial_investment, 2),
        "present_value_cash_flows": round(sum(pv_cash_flows), 2),
        "terminal_value": round(terminal_value, 2),
        "present_value_terminal": round(pv_terminal, 2),
        "illustrative_intrinsic_value": round(intrinsic_value, 2),
        "npv": round(npv, 2),
        "margin_of_safety": round(margin_of_safety, 4) if margin_of_safety is not None else None,
        "simple_total_cash_roi": round(simple_roi, 4),
        "assumptions": {
            "discount_rate": rate,
            "terminal_growth_rate": growth,
            "cash_flows_are_estimates": True,
            "taxes_debt_working_capital_and_dilution_included": False,
        },
        "warning": "Illustrative scenario only. Outputs depend entirely on user assumptions; not investment advice or a recommendation to buy or sell.",
    }


@router.get("/qa/checklist")
async def qa_checklist() -> dict:
    return {
        "status": "IMPLEMENTADO",
        "pipeline_status": "PENDIENTE",
        "checks": [
            {"id": "unit", "label": "Unit tests", "status": "PENDIENTE"},
            {"id": "api", "label": "API contract tests", "status": "PENDIENTE"},
            {"id": "a11y", "label": "Accessibility audit", "status": "PENDIENTE"},
            {"id": "e2e", "label": "Browser end-to-end tests", "status": "PENDIENTE"},
            {"id": "android", "label": "Android device validation", "status": "PENDIENTE"},
            {"id": "release", "label": "Signed release and deployment", "status": "PENDIENTE"},
        ],
        "note": "This endpoint reports the checklist; it does not execute tests or deploy software.",
    }
