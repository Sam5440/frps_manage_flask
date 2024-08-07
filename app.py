from flask import Flask, render_template, request, redirect, url_for, session
import configparser, os, shutil, datetime
from flask_session import Session

# 读取配置文件
def load_app_config(filename='config.ini'):
    config = configparser.ConfigParser()
    config.read(filename)
    return config

app_config = load_app_config()

app = Flask(__name__)
app.secret_key = app_config['flask']['secret_key']
app.config['SESSION_TYPE'] = app_config['flask']['session_type']
Session(app)

# 从配置文件中获取用户名和密码
USERNAME = app_config['auth']['username']
PASSWORD = app_config['auth']['password']

def read_config():
    config = configparser.ConfigParser()
    config.read('frpc.ini')
    return config

def write_config(config, filename='frpc.ini', backup_folder='backup'):
    # 确保备份文件夹存在
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    # 获取当前时间并格式化
    current_time = datetime.datetime.now().strftime('%Y%m%d%H%M')

    # 构建备份文件路径
    backup_filename = os.path.join(backup_folder, f'{current_time}_{filename}')

    # 读取原文件内容并创建备份
    if os.path.exists(filename):
        shutil.copy2(filename, backup_filename)
        print(f"Backup created at {backup_filename}")

    # 写入新的配置文件内容
    with open(filename, 'w') as configfile:
        config.write(configfile)
        print(f"New configuration written to {filename}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    wrap.__name__ = f.__name__
    return wrap

@app.route('/')
@login_required
def index():
    config = read_config()
    print(config)
    common_config = config['common'] if 'common' in config else {}
    common_config_str = '\n'.join(f'{key} = {value}' for key, value in common_config.items())
    return render_template('index.html', config=config, common_config=common_config_str)

@app.route('/update_common', methods=['POST'])
@login_required
def update_common():
    config = read_config()
    common_config = request.form['common_config']
    config['common'] = dict(line.split('=', 1) for line in common_config.splitlines() if '=' in line)
    write_config(config)
    return redirect(url_for('index'))

@app.route('/update/<section>', methods=['POST'])
@login_required
def update(section):
    config = read_config()
    new_section = request.form['new_section']
    type_ = request.form['type']
    local_ip = request.form['local_ip']
    local_port = request.form['local_port']
    remote_port = request.form['remote_port']
    custom_domains = request.form['custom_domains']

    if new_section and new_section not in config:
        config.remove_section(section)
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
@login_required
def delete(section):
    config = read_config()
    config.remove_section(section)
    write_config(config)
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
@login_required
def add():
    config = read_config()
    new_section = request.form['new_section']
    type_ = request.form['type']
    custom_type = request.form.get('custom_type', '').strip()
    local_ip = request.form['local_ip']
    local_port = request.form['local_port']
    remote_port = request.form['remote_port']
    custom_domains = request.form['custom_domains']

    if type_ == 'other' and custom_type:
        type_ = custom_type

    suffix = f'_{type_}'
    if not new_section.endswith(suffix):
        new_section = new_section.rstrip('_tcp').rstrip('_udp').rstrip(f'_{type_}') + suffix

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

@app.route('/debug', methods=['GET', 'POST'])
@login_required
def debug():
    if request.method == 'POST':
        new_config_content = request.form['config_content']
        with open('frpc.ini', 'w') as configfile:
            configfile.write(new_config_content)
        return redirect(url_for('debug'))

    with open('frpc.ini', 'r') as configfile:
        config_content = configfile.read()

    return render_template('debug.html', config_content=config_content)

if __name__ == '__main__':
    port = int(app_config['flask']['port'])
    host = app_config['flask']['host']
    app.run(debug=True, port=port, host=host)