import discord
from dotenv import load_dotenv
load_dotenv()
import os
import requests
import extcolors
from PIL import Image
import sqlite3
import json
con = sqlite3.connect("bot.db")
cur = con.cursor()

intents = discord.Intents.default()
intents.message_content = True

# Functions

def get_country_embed(pais):
    response_raw = requests.get(f"https://restcountries.com/v3.1/name/{pais}")
    data = response_raw.json()
    capital = data[0]['capital'][0]
    poblacion = data[0]['population']
    region = data[0]['region']
    bandera = data[0]['flags']['png']
    image = Image.open(requests.get(bandera, stream=True).raw)

    colors = extcolors.extract_from_image(image)
    color1 = colors[0][0][0][0]
    color2 = colors[0][0][0][1]
    color3 = colors[0][0][0][2]

    embed = discord.Embed(
        title=pais.capitalize(),
        description="Informacion del pais",
        color=discord.Colour.from_rgb(color1, color2, color3)
    )
    embed.add_field(name="Capital", value=capital, inline=True)
    embed.add_field(name="Poblacion", value=f"{'{:,}'.format(poblacion)}", inline=True)
    embed.add_field(name="Region", value=region, inline=True )
    embed.set_thumbnail(url=bandera)

    return embed

def get_matchs(name, teams):
    matchs = []
    for match in teams:
        if match['home_team_en'] == name:
            matchs.append(match)
        elif match['away_team_en'] == name:
            matchs.append(match)
    return matchs

def get_data(id, url):
    res = cur.execute("""
        SELECT token FROM users
        WHERE discord_id = ?
    """, [id])
    token = res.fetchone()[0]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    return response

def get_team(team_name, equipos):
    for equipo in equipos:
        if equipo["name_en"] == team_name:
            return equipo

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
            return

    if message.content.startswith('!calc'):
        operacion = message.content.split(' ')[1]
        def calc():
            try:
                if operacion.__contains__("+"):
                    num1 = float(operacion.split("+")[0])
                    num2 = float(operacion.split("+")[1])
                    return num1 + num2
                elif operacion.__contains__("-"):
                    num1 = float(operacion.split("-")[0])
                    num2 = float(operacion.split("-")[1])
                    return num1 - num2
                elif operacion.__contains__("*"):
                    num1 = float(operacion.split("*")[0])
                    num2 = float(operacion.split("*")[1])
                    return num1 * num2
                elif operacion.__contains__("/"):
                    num1 = float(operacion.split("/")[0])
                    num2 = float(operacion.split("/")[1])
                    return num1 / num2
                else:
                    return "Datos invalidos"
            except ValueError:
                    return "Numeros invalidos"
        
        resultado = calc()

        if isinstance(resultado, str):
            await message.channel.send(resultado)
        else:
            await message.channel.send(f"""
            El resultado es: {calc()}
            """)

    if message.content.startswith('!registro'):
            try:
                id = message.author.id
                name = message.content.split(" ")[1]
                email = message.content.split(" ")[2]
                password = message.content.split(" ")[3]
                confirm_password = message.content.split(" ")[4]

                user = {
                    "name": name,
                    "email": email,
                    "password": password,
                    "passwordConfirm": confirm_password
                }
                json_body = json.dumps(user)
                headers = {
                    "Content-Type": "application/json"
                }
                response = requests.post("http://api.cup2022.ir/api/v1/user", data=json_body, headers=headers)
                error = response.json()
                if str(error["message"]).__contains__("duplicate"):
                    return await message.channel.send(f"<@{id}> ya esta registrado")
                elif str(error["message"]).__contains__("the minimum allowed length"):
                    return await message.channel.send(f"<@{id}> contraseña incorrecta")
                elif str(error["message"]).__contains__("valid email"):
                    return await message.channel.send(f"<@{id}> email incorrecto, verifique.")
                cur.execute("""
                    INSERT INTO users (discord_id, name, email, password) VALUES(?, ?, ?, ?)
                """, (id, name, email, password))
                con.commit()
                await message.channel.send(f"Registro satisfactorio! <@{id}>")
            except sqlite3.IntegrityError:
                await message.channel.send(f"<@{id}> tu usuario ya se encuentra registrado!")
            except:
                await message.channel.send(f"<@{id}> datos incompletos, intentelo de nuevo!")

    if message.content.startswith('!iniciar'):
        try:
            id = message.author.id
            res = cur.execute("""
                SELECT email, password FROM users
                WHERE discord_id = ? 
            """, [id])
            data = res.fetchone()
            credentials = {
                "email": data[0],
                "password": data[1]
            }
            json_body = json.dumps(credentials)
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post("http://api.cup2022.ir/api/v1/user/login", data=json_body, headers=headers).json()
            token = response["data"]["token"]
            cur.execute("""
                UPDATE users
                SET token = ?
                WHERE discord_id = ? 
                """, (token, id))
            con.commit()
        except:
            await message.channel.send(f"<@{id}> Iniciaste sesion. Puedes usar todos las funciones del bot" )
        #except:
           # await message.channel.send(f"<@{id}> Tienes que volver a iniciar sesion. Corre el comando correctamente de !iniciar." )
    if message.content.startswith('!eliminar'):
        try:
            id = message.author.id
            #BUSCAR USUARIO
            res = cur.execute("""
                SELECT * FROM users WHERE discord_id = ? 
            """, (id,))
            user = res.fetchone()[0]
            print(user)
            #eliminar usuario
            cur.execute("""
                DELETE FROM users WHERE discord_id = ? 
                """, (id,))
            con.commit()
        except:
            await message.channel.send(f"Usuario eliminado! <@{id}>")
            if response.status_code == 401:
                await message.channel.send("Tienes que volver a iniciar sesion. Corre el comando !iniciar.")
        
    if message.content.startswith('!actualizar'):
       try:
            id = message.author.id
            #buscar usuario
            res = cur.execute("""
                SELECT * FROM users WHERE discord_id = ? 
            """, (id,))
            user = res.fetchone()[0]
            if len(message.content.split(" ")) == 2:
                pais = message.content.split(" ")[1]
                cur.execute("""
                    UPDATE users
                    SET country = ?  
                    WHERE discord_id = ? 
                """, (pais, id))
                con.commit()
            else:
                pais = message.content.split(" ")[1]
                name = message.content.split(" ")[2]
                #actualizar usuario
                cur.execute("""
                    UPDATE users
                    SET 
                        country = ?,
                        name = ?
                    WHERE discord_id = ? 
                """, (pais, name, id))
                con.commit()
            await message.channel.send(f"Usuario actualizado con exito! <@{id}>")
       except:
            await message.channel.send(f"<@{id}> el usuario no existe!")

    if message.content.startswith('!pais'):
        try:
            response_message = await message.channel.send("Cargando...")
            pais = str(message.content.split(' ')[1])
            embed = get_country_embed(pais)
            await response_message.delete()
            await message.channel.send(embed=embed)
        except IndexError:
            id = str(message.author.id)
            res = cur.execute("""
                SELECT country FROM users
                WHERE discord_id = ?
            """, [id])
            country = res.fetchone()[0]
            embed = get_country_embed(country)
            await response_message.delete()
            await message.channel.send(embed=embed)
        except:
            await response_message.delete()
            await message.channel.send("El pais no existe")

    if message.content.startswith('!equipo'): 
            pais = str(message.content.split(" ")[1]).capitalize()
            id = message.author.id
            response =get_data("http://api.cup2022.ir/api/v1/team")
            if response.status_code == 401:
                await message.channel.send("Tienes que volver a iniciar sesion. Corre el comando !iniciar.")
            equipos = response.json()["data"]
            informacion_equipo = get_team(pais, equipos)
            print(informacion_equipo)
            if informacion_equipo is None:
                await message.channel.send(f"<@{id}> {pais} no clasifico al mundial.")

    if message.content.startswith("!partidos"):
        try:
            id = message.author.id
            pais = str(message.content.split(" ")[1]).capitalize()
            response = get_data(id, "http://api.cup2022.ir/api/v1/match")
            if response.status_code == 401:
                await message.channel.send("Tienes que volver a iniciar sesion. Corre el comando !iniciar.")
            equipos = response.json()["data"]
            matchs = get_matchs(pais, equipos)
            if len(matchs) == 0:
                await message.channel.send(f"<@{id}> {pais} no clasifico al mundial.")
            for match in matchs:
                home_team = match['home_team_en']
                away_team = match['away_team_en']
                date = match['local_date']
                home_goals = match['home_score']
                away_goals = match['away_score']
                flag = match['home_flag']
                image = Image.open(requests.get(flag, stream=True).raw)

                colors = extcolors.extract_from_image(image)
                color1 = colors[0][0][0][0]
                color2 = colors[0][0][0][1]
                color3 = colors[0][0][0][2]

                embed=discord.Embed(
                    title=f"{home_team} vs {away_team}",
                    color=discord.Colour.from_rgb(color1, color2, color3)
                )
                embed.add_field(name='Casa', value=home_team)
                embed.add_field(name='Visitante', value=away_team)
                embed.add_field(name='Fecha', value=date)
                embed.add_field(name=f'Goles {home_team}', value=home_goals)
                embed.add_field(name=f'Goles {away_team}', value=away_goals)
                embed.set_thumbnail(url=flag)
                await message.channel.send(embed=embed)
        except:
            await message.channel.send(f"<@{id}> tienes que colocar 1 pais.")

    if message.content.startswith('!ayuda'):
        try:
            await message.channel.send('''
            **Comandos**:
            \n**!registro**: Para iniciar en el bot tienes que registrarte. Ejemplo: !registro nombre correo contraseña cofirmarcontraseña. La contraseña debe ser de 10 caracteres y debe contener numeros y al menos 1 letra.
            \n**!iniciar**: Si ya estas registrado, podras usar el bot.
            \n**!eliminar**: Si ya estas registrado, elimina tu usuario o al que registraste recientemente.
            \n**!Actualizar**: Si ya estas registrado, modifica el nombre y el pais de la informacion del usuario.
            \n**!pais**: Acepta un solo parametro el nombre del pais en ingles y muestra la información del mismo.
            \n**!ayuda**: Muestra la infomración del bot.
            ''')
        except: 
            await message.channel.send('''Ingrese el comando de ayuda correctamente''' )

client.run(os.environ["TOKEN"])
