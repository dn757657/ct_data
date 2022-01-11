""" this is just a file to house the displays db structure"""

# displays & dashboards section
# for integer columns variable input enter 0
# for text column variable input enter var
display_types = """ CREATE TABLE IF NOT EXISTS display_types (
                                dt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                x_min TEXT,
                                x_resolution INTEGER
                                x_max TEXT,
                                x_window_size INTEGER,
                                x_window_unit TEXT,
                                graph_type TEXT NOT NULL,
                                proj_type TEXT
                                UNIQUE(x_min, x_resolution, x_max, x_window_size, x_window_unit, graph_type)
        
                            ); """

dashboards = """ CREATE TABLE IF NOT EXISTS dashboards (
                                dash_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                dash_desc TEXT NOT NULL,
                                dash_date DATETIME DEFAULT CURRENT_TIMESTAMP
        
                            ); """

displays_dashboards = """ CREATE TABLE IF NOT EXISTS cm_dashboards (
                                dt_id INTEGER,
                                dash_id INTEGER,
                                UNIQUE(di_id, dash_id)
                                FOREIGN KEY (dt_id) REFERENCES display_types (dt_id) ON DELETE CASCADE ON UPDATE CASCADE,
                                FOREIGN KEY (dash_id) REFERENCES dashboards (dash_id) ON DELETE CASCADE ON UPDATE CASCADE
        
                            ); """

# display types and link tables
cm_records = """ CREATE TABLE IF NOT EXISTS cm_records (
                                cm_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                cm_target REAL NOT NULL,
                                cm_resolution,
                                cm_type TEXT NOT NULL CHECK(cm_type IN ('budget','goal','account')),
                                cm_desc TEXT,
                                g_profile INTEGER,
                                acc_date DATETIME
                                
                            ); """


cm_sources = """ CREATE TABLE IF NOT EXISTS cm_sources (
                                cm_id INTEGER NOT NULL,
                                source_table TEXT NOT NULL CHECK (source_table in (SELECT name FROM sqlite_master WHERE type='table)),
                                source_col TEXT NOT NULL,
                                source_cond TEXT CHEK(source_cond IN ('=', 'LIKE', '<=', '>=')),
                                source_id INTEGER,
                                FOREIGN KEY (cm_id) REFERENCES cm_records (cm_id) ON DELETE CASCADE ON UPDATE CASCADE
                                
                            ); """

DISPLAY_TABLES = [display_types, dashboards, displays_dashboards, cm_records, cm_sources]
