from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import pandas as pd

driver = webdriver.Chrome()
driver.get("https://bbtips.com.br/inicio")


def login(email, senha, driver):
    driver.find_element(By.ID, 'email').send_keys(email)
    driver.find_element(By.ID, 'password').send_keys(senha)
    driver.find_element(
        By.XPATH, '/html/body/app-root/app-auth/div[1]/div[2]/form/div[3]/div[1]/button').click()
    driver.maximize_window()


email = 'XXX'
senha = 'XXX'
sleep(5)
login(email, senha, driver)
print('login')
sleep(10)

driver.get('https://bbtips.com.br/futebol/horarios')
print('waiting...')
sleep(10)


driver.find_elements(By.CLASS_NAME, 'link')[-1].click()
print('waiting...')
sleep(20)

print('starting')

campeonatos = []

done = 5
while done > 0:
    try:
        for i in range(1, 5):
            xpath_base = f'/html/body/app-root/app-horarios/main/section/div[2]/div[{i}]/app-tabela-futebol'
            campeonatos.append(
                {'nome': driver.find_element(By.XPATH, f'/html/body/app-root/app-horarios/main/section/div[2]/div[{i}]/app-tabela-futebol/h3').text,
                 'linhas': driver.find_elements(By.XPATH, f'{xpath_base}/table/tbody/*')[:-1],
                 'minutos': [x.text for x in driver.find_elements(By.XPATH, f'{xpath_base}/table/thead/tr[3]/*')],
                 })

        for i, campeonato in enumerate(campeonatos):
            campeonato['resultados'] = []
            for linha in campeonato['linhas']:
                tds = linha.find_elements(By.XPATH, "./child::*")
                hora = tds[0].text
                for mi, td in enumerate(tds[1:-2]):
                    if td.text != '':
                        campeonato['resultados'].append(
                            {'horario': f"{hora}:{campeonato['minutos'][mi+1]}", 'placar': [int(x[0]) for x in td.text.split('-')]})

            campeonato.pop('linhas')
            campeonato.pop('minutos')
        done = 0
    except:
        done -= 1
        print('Error')

print('finish reading')


def ambas_marcam(x):
    if x[0] > 0 and x[1] > 0:
        return True
    return False


def ambas_nao_marcam(x):
    if x[0] == 0 or x[1] == 0:
        return True
    return False


def over_2_5(x):
    if x[0] + x[1] > 2:
        return True
    return False


def over_3_5(x):
    if x[0] + x[1] > 3:
        return True
    return False


def casa_vence(x):
    if x[0] > x[1]:
        return True
    return False


def visitante_vence(x):
    if x[0] < x[1]:
        return True
    return False


def empate(x):
    if x[0] == x[1]:
        return True
    return False


def visitante_2(x):
    if 2 == x[1]:
        return True
    return False


def new_placar(x):
    return f'{x[0]}-{x[1]}'


def get_3_next(df, i):
    return df.iloc[i+1:i+4]


def set_results(row, i, n_entrada, df):
    next_3_games = get_3_next(df, i+n_entrada)
    r = {'hora_inicio_padrao': row.hora,
         'placar_inicio_padrao': row.placar,
         'n_jogos': n_entrada,
         f'hora_apos_jogo': df.iloc[i+n_entrada].hora,
         f'placar_apos_jogo': df.iloc[i+n_entrada].placar,
         'pago_ambas': False,
         'pago_over_2_5': False,
         'pago_over_3_5': False
         }
    c = 1
    for _, v in next_3_games.iterrows():
        if v.ambas_marcam:
            r['pago_ambas'] = v.ambas_marcam
        if v.over_2_5:
            r['pago_over_2_5'] = v.over_2_5
        if v.over_3_5:
            r['pago_over_3_5'] = v.over_3_5

        r['tiro-'+str(c)] = {'hora': v.hora, 'placar': v.placar,
                             'ambas_marcam': v.ambas_marcam, 'over_2_5': v.over_2_5, 'over_3_5': v.over_3_5, }
        c += 1
    return r


dfs = []

for camp in campeonatos:
    df = pd.DataFrame(camp['resultados'])
    df['casa'] = [x[0] for x in df['placar']]
    df['visitante'] = [x[1] for x in df['placar']]
    df['ambas_marcam'] = False
    df['ambas_nao_marcam'] = False
    df['over_2_5'] = False
    df['over_3_5'] = False

    df['ambas_marcam'] = df['placar'].apply(ambas_marcam)
    df['ambas_nao_marcam'] = df['placar'].apply(ambas_nao_marcam)
    df['over_2_5'] = df['placar'].apply(over_2_5)
    df['over_3_5'] = df['placar'].apply(over_3_5)
    df['casa_vence'] = df['placar'].apply(casa_vence)
    df['visitante_vence'] = df['placar'].apply(visitante_vence)
    df['empate'] = df['placar'].apply(empate)
    df['visitante_2'] = df['placar'].apply(visitante_2)
    df['placar'] = df['placar'].apply(new_placar)

    df['hora'] = pd.to_datetime(
        df['horario'], format='%H:%M').dt.time
    df = df.sort_values('hora', ascending=True)

    df.drop(
        ['horario'], axis=1, inplace=True)
    df = df[['hora', 'placar', 'casa', 'visitante', 'ambas_marcam', 'ambas_nao_marcam', 'over_2_5',
             'over_3_5', 'casa_vence', 'visitante_vence', 'empate', 'visitante_2']].reset_index(drop=True)
    dfs.append({'name': camp['nome'], 'df': df})

a_r = []
for df in dfs:
    result = []

    for i, row in df['df'].iterrows():
        if row.casa_vence:
            try:
                if df['df'].iloc[i+1].visitante_2:
                    result.append(set_results(row, i, 1, df['df']))

                elif df['df'].iloc[i+2].visitante_2:
                    result.append(set_results(row, i, 2, df['df']))
            except Exception as ex:
                print(ex)
                pass
    a_r.append((df['name'], result))

for k, a in enumerate(a_r):
    pd.DataFrame(a_r[k][1]).to_excel('dado'+a[0]+'.xlsx', index=False)

driver.close()
