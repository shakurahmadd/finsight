from db.database import SessionLocal
from db.models import DkKnowledge, MacroIndicator, SectorMacroMapping


session = SessionLocal()

if session.query(DkKnowledge).count() == 0:
    dk_knowledge_rows = [
        # Technology
        DkKnowledge(sector='Technology', metric_name='pe_ratio', sector_avg=28, std_dev=8, upper_threshold=45, lower_threshold=15, importance=1.0),
        DkKnowledge(sector='Technology', metric_name='pb_ratio', sector_avg=7, std_dev=3, upper_threshold=12, lower_threshold=2, importance=1.0),
        DkKnowledge(sector='Technology', metric_name='revenue_growth', sector_avg=12, std_dev=6, upper_threshold=25, lower_threshold=3, importance=1.0),
        DkKnowledge(sector='Technology', metric_name='profit_margin', sector_avg=22, std_dev=8, upper_threshold=35, lower_threshold=8, importance=1.0),
        DkKnowledge(sector='Technology', metric_name='debt_to_equity', sector_avg=0.5, std_dev=0.3, upper_threshold=1.2, lower_threshold=0.0, importance=1.0),
        # Financials
        DkKnowledge(sector='Financials', metric_name='pe_ratio', sector_avg=12, std_dev=3, upper_threshold=18, lower_threshold=6, importance=1.0),
        DkKnowledge(sector='Financials', metric_name='pb_ratio', sector_avg=1.3, std_dev=0.4, upper_threshold=2.2, lower_threshold=0.6, importance=1.0),
        DkKnowledge(sector='Financials', metric_name='revenue_growth', sector_avg=5, std_dev=3, upper_threshold=12, lower_threshold=0, importance=1.0),
        DkKnowledge(sector='Financials', metric_name='profit_margin', sector_avg=18, std_dev=6, upper_threshold=30, lower_threshold=8, importance=1.0),
        DkKnowledge(sector='Financials', metric_name='debt_to_equity', sector_avg=2.0, std_dev=0.8, upper_threshold=4.0, lower_threshold=0.5, importance=1.0),
        # Energy
        DkKnowledge(sector='Energy', metric_name='pe_ratio', sector_avg=14, std_dev=5, upper_threshold=25, lower_threshold=5, importance=1.0),
        DkKnowledge(sector='Energy', metric_name='pb_ratio', sector_avg=1.8, std_dev=0.6, upper_threshold=3.0, lower_threshold=0.8, importance=1.0),
        DkKnowledge(sector='Energy', metric_name='revenue_growth', sector_avg=6, std_dev=8, upper_threshold=20, lower_threshold=-10, importance=1.0),
        DkKnowledge(sector='Energy', metric_name='profit_margin', sector_avg=10, std_dev=5, upper_threshold=20, lower_threshold=2, importance=1.0),
        DkKnowledge(sector='Energy', metric_name='debt_to_equity', sector_avg=0.8, std_dev=0.4, upper_threshold=1.8, lower_threshold=0.1, importance=1.0),
        # Consumer
        DkKnowledge(sector='Consumer', metric_name='pe_ratio', sector_avg=22, std_dev=6, upper_threshold=35, lower_threshold=10, importance=1.0),
        DkKnowledge(sector='Consumer', metric_name='pb_ratio', sector_avg=4.0, std_dev=1.5, upper_threshold=7.0, lower_threshold=1.5, importance=1.0),
        DkKnowledge(sector='Consumer', metric_name='revenue_growth', sector_avg=7, std_dev=4, upper_threshold=15, lower_threshold=1, importance=1.0),
        DkKnowledge(sector='Consumer', metric_name='profit_margin', sector_avg=12, std_dev=5, upper_threshold=22, lower_threshold=3, importance=1.0),
        DkKnowledge(sector='Consumer', metric_name='debt_to_equity', sector_avg=0.9, std_dev=0.4, upper_threshold=2.0, lower_threshold=0.1, importance=1.0),
        # Healthcare
        DkKnowledge(sector='Healthcare', metric_name='pe_ratio', sector_avg=20, std_dev=7, upper_threshold=35, lower_threshold=8, importance=1.0),
        DkKnowledge(sector='Healthcare', metric_name='pb_ratio', sector_avg=3.5, std_dev=1.5, upper_threshold=6.5, lower_threshold=1.0, importance=1.0),
        DkKnowledge(sector='Healthcare', metric_name='revenue_growth', sector_avg=8, std_dev=5, upper_threshold=18, lower_threshold=1, importance=1.0),
        DkKnowledge(sector='Healthcare', metric_name='profit_margin', sector_avg=15, std_dev=7, upper_threshold=28, lower_threshold=3, importance=1.0),
        DkKnowledge(sector='Healthcare', metric_name='debt_to_equity', sector_avg=0.6, std_dev=0.3, upper_threshold=1.4, lower_threshold=0.0, importance=1.0),
    ]
    session.add_all(dk_knowledge_rows)
    session.commit()
    print("dk_knowledge seeded.")
else:
    print("dk_knowledge already seeded, skipping.")


if session.query(MacroIndicator).count() == 0:
    macro_rows = [
    MacroIndicator(indicator_name = 'federal_funds_rate', current_value = 4.33, change = -0.25, importance=1.0),
    MacroIndicator(indicator_name = 'cpi_inflation', current_value = 2.8, change = 0.1, importance = 1.0),
    MacroIndicator(indicator_name = 'gdp_growth', current_value = 2.3, change = -0.1, importance = 1.0),
    MacroIndicator(indicator_name = 'unemployment_rate', current_value = 4.1, change = 0.1, importance = 1.0),
    MacroIndicator(indicator_name = 'ten_year_treasury', current_value = 4.5, change = 0.2, importance=1.0)]

    session.add_all(macro_rows)
    session.commit()
    print("macro_indicators seeded.")
else:
    print('macro_indicators already seeded, skipping.')



if session.query(SectorMacroMapping).count() == 0:
    sector_macro_map = [
        SectorMacroMapping(sector = 'Financials', indicator_id = 1),
        SectorMacroMapping(sector = 'Financials', indicator_id = 5),

        SectorMacroMapping(sector = 'Technology', indicator_id = 1),
        SectorMacroMapping(sector = 'Technology', indicator_id = 5),

        SectorMacroMapping(sector = 'Consumer', indicator_id = 2),
        SectorMacroMapping(sector = 'Consumer', indicator_id = 4),

        SectorMacroMapping(sector = 'Energy', indicator_id = 3),
        SectorMacroMapping(sector = 'Energy', indicator_id = 5),

        SectorMacroMapping(sector = 'Healthcare', indicator_id = 2),
        SectorMacroMapping(sector = 'Healthcare', indicator_id = 3)
    ]

    session.add_all(sector_macro_map)
    session.commit()
    print("sector-macro map seeded.")
else:
    print('mapping alreadt seeded, skipping.')




session.close()
