from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Import necessary functions from other modules (placeholders for now)
# from expenses.utils import analyze_expenses
# from goals.utils import create_savings_plan
# from loans.utils import check_loan_eligibility
# from investments.utils import simulate_investment

@login_required
def agent_home(request):
    """View for the AI assistant interface."""
    context = {}
    return render(request, "agent_interface/agent_home.html", context)

@csrf_exempt  # Use CSRF protection appropriately in production
@login_required
def process_prompt(request):
    """API endpoint to process user prompts via the AI agent."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            prompt = data.get("prompt", "").lower()
            
            if not prompt:
                return JsonResponse({"error": "Prompt cannot be empty."}, status=400)
            
            # Parse the prompt and determine the action
            action, params = parse_prompt(prompt)
            
            # Execute the action based on the parsed result
            response_data = execute_action(request.user, action, params)
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            # Log the error in a real application
            print(f"Error processing prompt: {e}")
            return JsonResponse({"error": "An error occurred while processing your request."}, status=500)
            
    return JsonResponse({"error": "Invalid request method."}, status=405)

def parse_prompt(prompt):
    """Rule-based parser to understand the user prompt and determine the action."""
    prompt = prompt.lower()
    
    # Keywords for different modules
    expense_keywords = ["expense", "spending", "spent", "budget", "cost", "pay", "paid"]
    loan_keywords = ["loan", "borrow", "credit", "mortgage", "finance", "debt"]
    goal_keywords = ["goal", "save", "saving", "target", "plan", "achieve"]
    investment_keywords = ["invest", "investment", "stock", "bond", "crypto", "portfolio", "return", "dca"]
    credit_keywords = ["credit score", "score", "report", "rating"]
    dashboard_keywords = ["dashboard", "summary", "overview", "net worth", "financial health"]
    
    # Simple rule-based matching
    if any(keyword in prompt for keyword in expense_keywords):
        # Example: Extract parameters like time frame or amount
        params = {"time_frame": "last 3 months"} # Placeholder
        return "analyze_expenses", params
        
    elif any(keyword in prompt for keyword in loan_keywords):
        # Example: Extract loan type or amount
        params = {"loan_type": "personal"} # Placeholder
        return "check_loan_eligibility", params
        
    elif any(keyword in prompt for keyword in goal_keywords):
        # Example: Extract goal amount or timeframe
        params = {"target_amount": 5000, "time_frame": "6 months"} # Placeholder
        return "create_savings_plan", params
        
    elif any(keyword in prompt for keyword in investment_keywords):
        # Example: Extract investment type or strategy
        params = {"strategy": "dca"} # Placeholder
        return "simulate_investment", params
        
    elif any(keyword in prompt for keyword in credit_keywords):
        params = {} # Placeholder
        return "get_credit_score", params
        
    elif any(keyword in prompt for keyword in dashboard_keywords):
        params = {} # Placeholder
        return "get_dashboard_summary", params
        
    else:
        # Default or fallback action
        return "unknown_action", {"original_prompt": prompt}

def execute_action(user, action, params):
    """Executes the determined action by calling the appropriate module function."""
    
    # Placeholder implementations - Replace with actual function calls
    if action == "analyze_expenses":
        # result = analyze_expenses(user, params.get("time_frame"))
        result = {"message": f"Analyzing expenses for {params.get("time_frame", "the default period")}...", "data": {"total_spent": 1500, "top_category": "Groceries"}}
        
    elif action == "check_loan_eligibility":
        # result = check_loan_eligibility(user, params.get("loan_type"), params.get("amount"))
        result = {"message": f"Checking eligibility for a {params.get("loan_type", "generic")} loan...", "data": {"eligible": True, "max_amount": 10000}}
        
    elif action == "create_savings_plan":
        # result = create_savings_plan(user, params.get("target_amount"), params.get("time_frame"))
        result = {"message": f"Creating savings plan for {params.get("target_amount", 0)} in {params.get("time_frame", "N/A")}...", "data": {"monthly_savings": 833.33}}
        
    elif action == "simulate_investment":
        # result = simulate_investment(user, params.get("strategy"))
        result = {"message": f"Simulating investment with {params.get("strategy", "default")} strategy...", "data": {"projected_value": 12000}}
        
    elif action == "get_credit_score":
        # Placeholder: Get score from credit module
        latest_credit = CreditHistory.objects.filter(user=user).order_by("-date").first()
        score = latest_credit.score if latest_credit else "Not Available"
        result = {"message": "Fetching your latest credit score...", "data": {"credit_score": score}}
        
    elif action == "get_dashboard_summary":
        # Placeholder: Get summary from dashboard module
        # assets = calculate_total_assets(user)
        # liabilities = calculate_total_liabilities(user)
        # net_worth = assets - liabilities
        result = {"message": "Fetching your financial summary...", "data": {"net_worth": 50000, "savings_rate": 15}}
        
    elif action == "unknown_action":
        result = {"message": "Sorry, I couldn\'t understand that request. Can you please rephrase?", "data": {}}
        
    else:
        result = {"message": "Action not implemented yet.", "data": {}}
        
    return result
