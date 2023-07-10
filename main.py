import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types
import json


class Message(StatesGroup):
    email = State()
    message = State()


bot = Bot(token="YOUR_TOKEN", parse_mode='HTML')  
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands='start')
async def start(message: types.Message):
    """The start panel of the telegram bot"""

    with open('data/admins.json') as file:  # Check whether the user is an administrator
        admins = json.load(file)
    
    for i in admins:
        if message.from_user.id == i['id_admin']:
            buttons = ['Админ. панель']
            kebyord = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kebyord.add(*buttons)
            break


        else:
            buttons = ['Написать в поддержку']
            kebyord = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kebyord.add(*buttons)


    await message.answer(f'Добро пожаловать', reply_markup=kebyord)


@dp.message_handler(Text(equals='Написать в поддержку'))
async def get_email(message: types.Message):
    """ask the user to enter an email"""
    
    await Message.email.set()
    await message.answer(f'Введите email')


@dp.message_handler(state=Message.email)
async def save_email(message: types.Message, state: FSMContext):
    """Save the email, ask the user to enter a message"""    
    async with state.proxy() as data:

        data['email'] = message.text
        with open('data/data.json') as file:
            users = json.load(file)


        flag = False
        for i in users:
            if i['id'] == message.from_user.id:  # If the user has already contacted technical support, we inform him that his message is being processed
                flag = True
                await message.answer(f'Вы уже отправили обращение в техподдержку. Если вы хотите дополнить обращение, просто напишите в чат.')
                await state.finish()
                break


            
        if flag == False:   # If the user has not contacted technical support, please enter a message
            await Message.message.set()
            await message.answer(f'Введите сообщение')


@dp.message_handler(state=Message.message)
async def process_contact_info(message: types.Message, state: FSMContext):
    """Save the message entered by the user"""
    
    async with state.proxy() as data:
        data['message'] = message.text

        with open('data/data.json') as file:
            users = json.load(file)

        if users != []:

            flag = False

            for i in users:

                if i["email"] == data["email"]:
                    i["message"].append(f'<b>К:</b> {data["message"]}\n')
                    flag = True
                    break


            if flag == False: 
                users.append({
                            "id": message.from_user.id, 
                            "email": data['email'],
                            "message": [f'<b>К:</b> {data["message"]}\n'],
                            "id_admin": None
                            })

        
        else:
            users.append({      
                        "id": message.from_user.id, 
                        "email": data['email'],
                        "message": [f'<b>К:</b> {data["message"]}\n'],
                        "id_admin": None
                        })
            
            
        with open(f'data/data.json', 'w') as file:
            json.dump(users, file, indent=3, ensure_ascii=False)

        
        with open('data/admins.json') as file2:
            admins = json.load(file2)


        for i in admins:
            await bot.send_message(str(i['id_admin']), f'<b>Новое сообщение</b>\nот: {data["email"]}\n\n{data["message"]}' )
                                                  
      
        await message.answer(f'Сообщение принято, ожидайте.\n')
        await state.finish()


@dp.message_handler(Text(equals='Админ. панель'))
async def admin_panel(message: types.Message):
    """Go to the admin panel"""

    buttons = ['Новые', 'Передать', 'Удалить', 'Мои обращения','История сообщений','С кем диалог?', 'Инструкция']
    kebyord = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kebyord.add(*buttons)

    await message.answer(f'Выберите дейтвие', reply_markup=kebyord)


@dp.message_handler(Text(equals='Новые'))
async def new(message: types.Message):
    """Showing new messages"""

    with open('data/data.json') as file:
        users = json.load(file)


    message_list = []

    for i in users: 
        if i['id_admin'] == None:
            message_list.append(i['email'])

    if message_list != []:
        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [InlineKeyboardButton((str(j)), callback_data=str(j) + "Take_new_user") for j in message_list]
        keyboard.add(*buttons)

        await bot.send_message(chat_id=message.chat.id, text='Выберите сообщение:', reply_markup=keyboard)

    
    else:       
        await bot.send_message(chat_id=message.chat.id, text='Нет новых сообщений')


@dp.message_handler(Text(equals='Передать'))
async def transfer(message: types.Message):
    """Display a list of administrators to choose who we want to transfer the client to"""

    with open('data/data.json') as file:
        users = json.load(file)

    my_users = []
    for i in users:
        if i["id_admin"] == message.chat.id:
            my_users.append(i['email'])

        else:
            continue
    
    if my_users != []:

        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [InlineKeyboardButton((str(j)), callback_data=str(j) + "Change_klient") for j in my_users]
        keyboard.add(*buttons)
        await bot.send_message(chat_id=message.chat.id, text='Выберите пользователя, которого хотите передать другому администатору', reply_markup=keyboard)


    else:
        await message.answer('У вас нет начатых диалогов с пользователями')
    

@dp.message_handler(Text(equals='Удалить'))
async def remove(message: types.Message):
    """Display a list of clients to finish the dialog"""

    with open('data/data.json') as file:
        users = json.load(file)

    my_users = []
    for i in users:
        if i["id_admin"] == message.chat.id:
            my_users.append(i['email'])

        else:
            continue
    
    if my_users != []:
        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [InlineKeyboardButton((str(j)), callback_data=str(j) + "Delite_chat") for j in my_users]
        keyboard.add(*buttons)

        await bot.send_message(chat_id=message.chat.id, text='Выберите пользователя, диалог с которым хотите завершить', reply_markup=keyboard)


    else:
        await message.answer('У вас нет начатых диалогов с пользователями')


@dp.message_handler(Text(equals='Мои обращения'))
async def my_appeals(message: types.Message):
    """Display a list of started dialogs"""

    with open('data/data.json') as file:
        users = json.load(file)

    my_users = []
    for i in users:
        if i["id_admin"] == message.chat.id:
            my_users.append(i['email'])

        else:
            continue
    
    if my_users != []:

        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [InlineKeyboardButton((str(j)), callback_data=str(j) + "Edit_chat") for j in my_users]
        keyboard.add(*buttons)
        await bot.send_message(chat_id=message.chat.id, text='Выберите пользователя на которого хотите переключится', reply_markup=keyboard)


    else:
        await message.answer('У вас нет начатых диалогов с пользователями')


@dp.message_handler(Text(equals='История сообщений'))
async def history(message: types.Message):
    """Display a list of started dialogs to show the message history"""

    with open('data/data.json') as file:
        users = json.load(file)

    my_users = []
    for i in users:
        if i["id_admin"] == message.chat.id:
            my_users.append(i['email'])

        else:
            continue
    
    if my_users != []:

        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [InlineKeyboardButton((str(j)), callback_data=str(j) + "Show_my_history") for j in my_users]
        keyboard.add(*buttons)
        await bot.send_message(chat_id=message.chat.id, text='Выберите пользователя историю сообщений с которым хотите посмотреть', reply_markup=keyboard)

    else:
        await message.answer('У вас нет начатых диалогов с пользователями')


@dp.message_handler(Text(equals='С кем диалог?'))
async def checking_the_dialog(message: types.Message):
    """Сheck who will receive the message if we write to the chat bot"""

    with open('data/plaseholders.json') as file2:
        ph = json.load(file2)
        
        for j in ph:
            if j['id_admin'] == message.chat.id:

                with open('data/data.json') as file:
                    users = json.load(file)

                if users != []:

                    flag = False
                    for i in users:

                        if i['id'] == j['id']:
                            flag = True
                            await message.answer(f'Сообщение которое вы отправите получит пользователь <b>"{i["email"]}"</b>')

                    if flag == False:

                        await message.answer(f'Нет выбранного диалога.\nВкладка <b>"Мои обращения"</b> для выбора диалога')
                            
                else:
                    await message.answer(f'Нет активных диалогов')


@dp.message_handler(Text(equals='Инструкция'))
async def back(message: types.Message):
   
    await message.answer(f'Во вкладке <b>"Новые"</b> отображаются входящие сообщения которые ещё не просмотрел ни один из администраторов. Чтобы начать диалог с пользователем нужно нажать на email отправителя.\n\nПосле того как вы нажали на email отправителя во вкладке <b>"Новые"</b>, вы можете передать пользователя другому администратору, нажав на вкладку <b>"Передать"</b>.\n\nВкладка <b>"Удалить"</b> чтобы завершить диалог с пользователем.\n\nНа вкладке <b>"Мои пользователи"</b> отображаются все начатые диалоги администратора. Между ними можно переключаться.\n<b>Важно</b> внимательно следить какой из пользователей получит сообщение. Для этого нужно нажать на вкладку <b>"C кем диалог?"</b>.\n\nТакже можно посмотреть историю сообщений с пользователем. Для этого нужно нажать <b>"История сообщений"</b>. После удаления история сообщений тоже удаляется.')

    
async def handle_callback(query: types.CallbackQuery):
    """Accept data from callback_data"""

    await query.message.edit_reply_markup()

    
    if "Take_new_user" in query.data:

        with open('data/data.json') as file:
            users = json.load(file)

        email = query.data.replace('Take_new_user', '')

        with open('data/admins.json') as file:
            admins = json.load(file)

        admins_list = []
        for i in admins:
            if i['id_admin'] == query.message.chat.id:

                my_name = i['name']

            else:
                admins_list.append(i['id_admin'])

        for a in admins_list:
            await bot.send_message(chat_id= a, text=f'Диалог с пользователем <b>{email}</b> забрал администратор <b>{my_name}</b> ')


        for i in users: 
            if i['email'] == email:

                i['id_admin'] = query.message.chat.id

                with open('data/plaseholders.json') as file2:
                    ph = json.load(file2)
        
                for j in ph:
                    if j['id_admin'] == query.message.chat.id:
                        j['id'] = i['id']
                
                with open(f'data/plaseholders.json', 'w') as file3:
                    json.dump(ph, file3, indent=3, ensure_ascii=False)

                with open(f'data/data.json', 'w') as file3:
                    json.dump(users, file3, indent=3, ensure_ascii=False)
 
                msg = "".join(i['message'])

                if len(msg) > 4000:
                    for x in range(0, len(msg), 4000):
                        await query.message.answer(f'От: <b>{i["email"]}</b>\n\n{msg[x:x+4000]}')
                
                else:
                    await query.message.answer(f'От: <b>{i["email"]}</b>\n\n{msg}')

                await query.message.answer(f'Введите ответ и пользователь <b>"{i["email"]}"</b> получит сообщение\n⏬⏬⏬')

   
    if  "Change_klient" in query.data:

        msg = query.data.replace('Change_klient', '')

        with open('data/admins.json') as file:
            admins = json.load(file)

        admins_list = []
        for i in admins:
            if i['id_admin'] == query.message.chat.id:
                continue

            else:
                admins_list.append(i['name'])

        keyboard = InlineKeyboardMarkup(row_width=1)
        buttons = [InlineKeyboardButton((str(j)), callback_data=str(j) + "Change_anmin" + " " + msg) for j in admins_list]
        keyboard.add(*buttons)

        await bot.send_message(chat_id=query.message.chat.id, text=f'Выберите администратора, которому хотите передать пользователя <b>{msg}</b>', reply_markup=keyboard)


    if  "Change_anmin" in query.data:

        msg = query.data.split(' ')
        email = msg[-1]
        name = msg[0].replace('Change_anmin', '')

        with open('data/admins.json') as file:
            admins = json.load(file)

        for k in admins:
            if name == k['name']:
                id_admin = k['id_admin']

            if k['id_admin'] == query.message.chat.id:
                my_name = k['name']

        with open('data/data.json') as file:
            users = json.load(file)

        for i in users: 
            if i['email'] == email:
                i["id_admin"] = id_admin

                with open(f'data/data.json', 'w') as file3:
                    json.dump(users, file3, indent=3, ensure_ascii=False)

                with open('data/plaseholders.json') as file4:
                        ph = json.load(file4)

                for j in ph:
                    if j['id_admin'] == query.message.chat.id and j['id']==i['id']:
                        j['id'] = None

                        with open(f'data/plaseholders.json', 'w') as file5:
                            json.dump(ph, file5, indent=3, ensure_ascii=False)

        await bot.send_message(chat_id=query.message.chat.id, text=f'Пользователь "<b>{email}</b>" был передан администратору <b>{name}</b>')
        await bot.send_message(chat_id=id_admin, text=f'Вам был передан пользователь "<b>{email}</b>" от администратора {my_name}')


    if  "Delite_chat" in query.data:

        msg = query.data.replace('Delite_chat', '')

        with open('data/data.json') as file:
            users = json.load(file)

        p = 0
        for i in users: 
            p+=1
            if msg == i['email']:

                with open('data/plaseholders.json') as file3:
                    ph = json.load(file3)
                
                for j in ph:
                    if j['id_admin'] == query.message.chat.id and j['id'] == i['id']:
                        j['id'] = None

                with open(f'data/plaseholders.json', 'w') as file4:
                    json.dump(ph, file4, indent=3, ensure_ascii=False)

                users.pop(p-1)

                with open(f'data/data.json', 'w') as file2:
                    json.dump(users, file2, indent=3, ensure_ascii=False)

                await bot.send_message(chat_id=query.message.chat.id, text=f'Обращение пользователя "<b>{i["email"]}</b>" было удалено')


    if  "Edit_chat" in query.data:
        msg = query.data.replace('Edit_chat', '')
        
        with open('data/data.json') as file:
            users = json.load(file)

        for i in users: 
            if i['email'] == msg:

                with open('data/plaseholders.json') as file2:
                    ph = json.load(file2)
                
                for j in ph:
                    if j['id_admin'] == query.message.chat.id:
                        j['id'] = i['id']
                    
                with open(f'data/plaseholders.json', 'w') as file3:
                    json.dump(ph, file3, indent=3, ensure_ascii=False)

                await query.message.answer(f'Вы переключились на пользователя <b>"{i["email"]}"</b>\nВведите ответ и он получит ваше сообщение\n⏬⏬⏬')


    if  "Show_my_history" in query.data:
        msg = query.data.replace('Show_my_history', '')

        with open('data/data.json') as file:
            users = json.load(file)

        for i in users: 
            if i['email'] == msg:

                message = ''.join(i['message'])

                if len(message) > 4000:
                    for x in range(0, len(message), 4000):
                        await query.message.answer(f'История сообщений с пользователем <b>{i["email"]}</b>\n\n{message[x:x+4000]}')
                
                else:
                    await query.message.answer(f'История сообщений с пользователем <b>{i["email"]}</b>\n\n{message}')

        
dp.register_callback_query_handler(handle_callback)


@dp.message_handler()
async def echo_message(msg: types.Message):
    """Catch the message and send it to the right user"""

    with open('data/admins.json') as file:
        admins = json.load(file)

    flag = False
    for i in admins:
        if i['id_admin'] == msg.chat.id:
            flag = True

            with open('data/plaseholders.json') as file2:
                ph = json.load(file2)
        
            for j in ph:

                if j["id_admin"] == i['id_admin'] and j['id'] != None:
                    with open('data/data.json') as file3:
                        users = json.load(file3)

                    for k in users:
                        if k['id'] == j['id']:
                            k["message"].append(f'<b>А:</b> {msg.text}\n')

                            with open(f'data/data.json', 'w') as file4:
                                json.dump(users, file4, indent=3, ensure_ascii=False)

                    await bot.send_message(chat_id=str(j["id"]), text=msg.text)
                    break
                

                if j['id'] == None and j["id_admin"] == i['id_admin']:
                    await msg.answer('Для начала выберите пользователя, которому нужно отправить сообщение. Сейчас никто не выбран')


    if flag == False:
        with open('data/data.json') as file3:
            users = json.load(file3)

        if users != []:
            for k in users:
                if k["id"] == msg.chat.id:
                    if k['id_admin'] == None:
                        k["message"].append(f'<b>К:</b> {msg.text}\n')

                        with open(f'data/data.json', 'w') as file4:
                            json.dump(users, file4, indent=3, ensure_ascii=False)
                            
                        for l in admins:
                            await bot.send_message(l, f'<b>Новое сообщение</b>\nот: {k["email"]}\n\n{msg.text}' )

                        break

                    else:
      
                        k["message"].append(f'<b>К:</b> {msg.text}\n')

                        with open(f'data/data.json', 'w') as file4:
                                json.dump(users, file4, indent=3, ensure_ascii=False)
                    
                        await bot.send_message(k['id_admin'], f'<b>Ваше сообщение</b>\nот: {k["email"]}\n\n{msg.text}' )
                        break



        else:

            await msg.answer('Чтобы создать обращение нажмите пожалуйста <b>"Написать в техподдержку"</b>')



if __name__ == '__main__':

    executor.start_polling(dp, skip_updates=True)
