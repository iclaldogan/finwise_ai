from django.contrib import admin
from .models import InvestmentType, Investment, InvestmentTransaction, InvestmentSimulation, SimulationResult


@admin.register(InvestmentType)
class InvestmentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'risk_level', 'avg_annual_return', 'volatility']
    list_filter = ['category', 'risk_level']
    search_fields = ['name', 'description']
    list_editable = ['risk_level', 'avg_annual_return', 'volatility']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Risk & Returns', {
            'fields': ('risk_level', 'avg_annual_return', 'volatility')
        }),
    )


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'investment_type', 'symbol', 'quantity', 'purchase_price', 'current_price', 'profit_loss_percentage', 'status']
    list_filter = ['status', 'investment_type', 'is_simulation', 'purchase_date']
    search_fields = ['name', 'symbol', 'user__email', 'notes']
    list_editable = ['current_price', 'status']
    date_hierarchy = 'purchase_date'
    raw_id_fields = ['user']
    autocomplete_fields = ['investment_type']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'investment_type', 'name', 'symbol')
        }),
        ('Purchase Details', {
            'fields': ('purchase_date', 'purchase_price', 'quantity')
        }),
        ('Current Status', {
            'fields': ('current_price', 'last_updated', 'status')
        }),
        ('Settings', {
            'fields': ('is_simulation', 'notes'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['last_updated']
    
    def profit_loss_percentage(self, obj):
        return f"{obj.profit_loss_percentage:.2f}%"
    profit_loss_percentage.short_description = 'P&L %'


@admin.register(InvestmentTransaction)
class InvestmentTransactionAdmin(admin.ModelAdmin):
    list_display = ['investment', 'transaction_type', 'date', 'price', 'quantity', 'fees']
    list_filter = ['transaction_type', 'date']
    search_fields = ['investment__name', 'investment__symbol', 'notes']
    date_hierarchy = 'date'
    raw_id_fields = ['investment']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('investment', 'transaction_type', 'date')
        }),
        ('Financial Details', {
            'fields': ('price', 'quantity', 'fees')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
    )


@admin.register(InvestmentSimulation)
class InvestmentSimulationAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'investment_type', 'strategy', 'initial_amount', 'duration_years', 'expected_return', 'created_at']
    list_filter = ['strategy', 'investment_type', 'created_at']
    search_fields = ['name', 'user__email']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user']
    autocomplete_fields = ['investment_type']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'investment_type', 'name', 'strategy')
        }),
        ('Investment Parameters', {
            'fields': ('initial_amount', 'periodic_amount', 'period_months', 'duration_years')
        }),
        ('Assumptions', {
            'fields': ('expected_return', 'volatility', 'inflation_rate')
        }),
    )


@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    list_display = ['simulation', 'year', 'month', 'investment_value', 'cumulative_investment', 'profit_loss']
    list_filter = ['simulation', 'year']
    search_fields = ['simulation__name']
    raw_id_fields = ['simulation']
    
    fieldsets = (
        ('Period', {
            'fields': ('simulation', 'year', 'month')
        }),
        ('Financial Results', {
            'fields': ('investment_value', 'cumulative_investment', 'profit_loss')
        }),
    ) 