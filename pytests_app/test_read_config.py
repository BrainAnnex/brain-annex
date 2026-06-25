import read_config
from configparser import ConfigParser



def test_load_config_data():

    config = ConfigParser()
    d = read_config.load_config_data(config)
    print(d)
    assert d == {'DB_COUNT': 2, 'DB_DEFAULT_INDEX': 1,
                'DB_HOST_1': 'bolt://localhost:7687', 'DB_USERNAME_1': 'neo4j', 'DB_PASSWORD_1': 'neo4j', 'DB_NICKNAME_1': 'remote (master)',
                'DB_HOST_2': 'bolt://THE_SERVER_IP_ADDRESS:7687', 'DB_USERNAME_2': 'neo4j', 'DB_PASSWORD_2': 'neo4j', 'DB_NICKNAME_2': 'local (slave)',
                'DEPLOYMENT': 'FLASK', 'PORT_NUMBER': 5000,
                'MEDIA_FOLDER': '/home/your_user_name/brain_annex_media/', 'UPLOAD_FOLDER': '/tmp/', 'LOG_FOLDER': '/bulk_import_done/',
                'INTAKE_FOLDER': '/bulk_import_intake/', 'OUTTAKE_FOLDER': '/bulk_import_done/',
                'PLUGINS': ['document', 'flash_card', 'header', 'image', 'note', 'recordset', 'site_link', 'timer_widget'],
                'INDEX_PDF_FILES': True, 'BRANDING': 'Brain Annex'}



def test__extract_par():
    config = ConfigParser()
    config.read(['config.defaults.ini', 'config.ini'])  # TODO: diversify testing, for just one or the other file
    SETTINGS = config['SETTINGS']

    assert read_config._extract_par("DB_COUNT", SETTINGS) == "2"
    assert read_config._extract_par("BRANDING", SETTINGS) == "Brain Annex"
