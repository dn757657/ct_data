""" this is just a file to house the displays db structure"""

# displays & dashboards section
# for integer columns variable input enter 0
# for text column variable input enter var
displays = """ CREATE TABLE IF NOT EXISTS displays (
                                di_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                disp_start TEXT,
                                disp_resolution REAL TEXT CHECK(disp_resolution IN ('year', 'month', 'week', 'day')),
                                disp_end TEXT,
                                disp_window_size INTEGER,
                                disp_window_unit TEXT CHECK(disp_window_unit IN ('year', 'month', 'week', 'day', 'var')),
                                disp_type TEXT NOT NULL,
                                graph_type TEXT NOT NULL,
                                proj_type TEXT
        
                            ); """

dashboards = """ CREATE TABLE IF NOT EXISTS dashboards (
                                dash_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                dash_desc TEXT NOT NULL,
                                dash_date DATETIME DEFAULT CURRENT_TIMESTAMP
        
                            ); """

displays_dashboards = """ CREATE TABLE IF NOT EXISTS displays_dashboards (
                                di_id INTEGER,
                                dash_id INTEGER,
                                UNIQUE(di_id, dash_id)
                                FOREIGN KEY (di_id) REFERENCES displays (di_id) ON DELETE CASCADE ON UPDATE CASCADE,
                                FOREIGN KEY (dash_id) REFERENCES dashboards (dash_id) ON DELETE CASCADE ON UPDATE CASCADE
        
                            ); """

# display types and link tables

dt_default = """ CREATE TABLE IF NOT EXISTS dt_default (
                                dt_default_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                dt_default_desc TEXT
                
                            ); """
dt_budget = """ CREATE TABLE IF NOT EXISTS dt_budget (
                                dt_budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                dt_b_target REAL NOT NULL,
                                dt_b_desc TEXT,
                                dt_b_type TEXT NOT NULL CHECK(dt_b_type IN ('year', 'month', 'week', 'day'))
        
                            ); """

dt_categories = """ CREATE TABLE IF NOT EXISTS dt_categories (
                                dt_default_id INTEGER,
                                dt_budget_id INTEGER,
                                dt_cat_id INTEGER,
                                FOREIGN KEY (dt_default_id) REFERENCES dt_default (dt_default_id) ON DELETE CASCADE ON UPDATE CASCADE,
                                FOREIGN KEY (dt_budget_id) REFERENCES dt_budget (dt_budget_id) ON DELETE CASCADE ON UPDATE CASCADE,
                                FOREIGN KEY (cat_id) REFERENCES categories (cat_id) ON DELETE CASCADE ON UPDATE CASCADE
                                
                            ); """

DISPLAY_TABLES = [displays, dashboards, displays_dashboards, dt_default, dt_budget, dt_categories]