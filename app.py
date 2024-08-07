from flask import Flask, render_template, request, redirect, url_for
import configparser

app = Flask(__name__)

# 配置文件路径
CONFIG_PATH = 'frpc.ini'

def read_config():
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(CONFIG_PATH, encoding='utf-8')
    return config

def write_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
        for section in config.sections():
            file.write(f'[{section}]\n')
            for key in config[section]:
                if config[section][key] is None or config[section][key].strip() == '':
                    file.write(f'# {key} =\n')
                else:
                    file.write(f'{key} = {config[section][key]}\n')
            file.write('\n')

@app.route('/')
def index():
    config = read_config()
    return render_template('index.html', config=config)

@app.route('/update/<section>', methods=['POST'])
def update(section):
    config = read_config()
    if section in config:
        new_section = request.form.get('new_section', section)
        if new_section != section:
            config[new_section] = config[section]
            del config[section]
            section = new_section
        for key in request.form:
            if key != 'new_section':
                config[section][key] = request.form[key]
        write_config(config)
    return redirect(url_for('index'))

@app.route('/add_option/<section>', methods=['POST'])
def add_option(section):
    config = read_config()
    if section in config:
        new_option = request.form['new_option']
        if new_option and new_option not in config[section]:
            config[section][new_option] = ''
        write_config(config)
    return redirect(url_for('index'))

@app.route('/delete_option/<section>/<option>', methods=['POST'])
def delete_option(section, option):
    config = read_config()
    if section in config and option in config[section]:
        del config[section][option]
        write_config(config)
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add():
    config = read_config()
    new_section = request.form['new_section']
    if new_section and new_section not in config:
        config[new_section] = {'type': '', 'local_ip': '', 'local_port': '', 'remote_port': '', 'custom_domains': ''}
        write_config(config)
    return redirect(url_for('index'))

@app.route('/delete/<section>', methods=['POST'])
def delete(section):
    config = read_config()
    if section in config:
        del config[section]
        write_config(config)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)