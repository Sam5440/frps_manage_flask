# 这是一个在网页修改frpc配置文件的程序
from flask import Flask, render_template, request, redirect, url_for
import configparser
import shutil
import os

app = Flask(__name__)

# 配置文件路径
CONFIG_PATH = 'frpc.ini'
BACKUP_PATH = 'frpc.ini.bak'

def backup_config():
    shutil.copyfile(CONFIG_PATH, BACKUP_PATH)

def restore_config():
    shutil.copyfile(BACKUP_PATH, CONFIG_PATH)

def read_config():
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(CONFIG_PATH, encoding='utf-8')
    return config

def read_common_section():
    with open(CONFIG_PATH, 'r') as file:
        lines = file.readlines()
        common_section = ''
        common_found = False
        common_lines = []
        other_lines = []
        for line in lines:
            if line.strip() == '[common]':
                common_found = True
            elif common_found and line.strip().startswith('['):
                common_found = False
            if common_found:
                common_lines.append(line)
            else:
                other_lines.append(line)
        common_section = ''.join(common_lines[1:]).rstrip()  # 去除"[common]"和最后的空行
        return common_section, other_lines

def write_config(config):
    backup_config()
    try:
        common_config, _ = read_common_section()
        with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
            file.write('[common]\n' + common_config + '\n\n')
            for section in config.sections():
                if section != 'common':
                    file.write(f'[{section}]\n')
                    for key in config[section]:
                        if config[section][key] is None or config[section][key].strip() == '':
                            file.write(f'# {key} =\n')
                        else:
                            file.write(f'{key} = {config[section][key]}\n')
                    file.write('\n')
        # 尝试读取新的配置文件，如果失败，恢复原始配置
        read_config()
    except Exception as e:
        restore_config()
        print(f"Failed to write config due to {str(e)}, restored to previous version.")

def write_common_section(common_config):
    backup_config()
    try:
        _, other_lines = read_common_section()
        common_lines = common_config.split('\n')
        with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
            file.write('[common]\n')
            for line in common_lines:
                file.write(line.rstrip() + '\n')
            file.write('\n')
            for line in other_lines:
                file.write(line)
        # 尝试读取新的配置文件，如果失败，恢复原始配置
        read_config()
    except Exception as e:
        restore_config()
        print(f"Failed to write common section due to {str(e)}, restored to previous version.")

@app.route('/')
def index():
    config = read_config()
    common_section, _ = read_common_section()
    return render_template('index.html', config=config, common_config=common_section)

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

@app.route('/update_common', methods=['POST'])
def update_common():
    common_config = request.form['common_config']
    write_common_section(common_config)
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add():
    config = read_config()
    new_section = request.form['new_section']
    type_ = request.form['type']
    local_ip = request.form['local_ip']
    local_port = request.form['local_port']
    remote_port = request.form['remote_port']
    custom_domains = request.form['custom_domains']

    if new_section and new_section not in config and type_ and local_ip and local_port and remote_port:
        config[new_section] = {
            'type': type_,
            'local_ip': local_ip,
            'local_port': local_port,
            'remote_port': remote_port,
            'custom_domains': custom_domains
        }
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
