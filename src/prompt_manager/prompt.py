import json
from prompt_manager.prompt_template import PromptTemplate
from task2prompt import task_prompt

class PromptHandler:
    RES_LIST = """你只能返回列表，不能包含其他任何解释"""  #。必须保证返回内容可以被Python的json.loads解析。
    RES_JSON = """你只能返回报文，不能包含其他任何解释"""
    ROLE1 = """You are an AI assistant that helps people find information."""
    #切换模型，chatgpt："chatgpt", davinci003: "davinci"
    gpt_model = "davinci"
    # ROLE2 = """You are an AI assistant that helps people complete computer task."""
    @classmethod
    def _get_message(cls,prompt):
        if cls.gpt_model == "chatgpt":
            return [
                {
                    "role": "system",
                    "content": f"{cls.ROLE1}"
                },
                {
                    "role": "user",
                    "content": f"{prompt}"
                }
            ]
        return prompt

    @classmethod
    def _get_message_extract(cls, prompt):
        # return prompt
        return [
            {
                "role": "system",
                "content": f"{cls.ROLE1}"
            },
            {
                "role": "user",
                "content": f"{prompt}"
            }
        ]

    @classmethod
    def _assemble_item_type_prompt(cls,item_type,input,recognize_item,item_type_name,example,all_include_response_example):
        # prompt = f"""你返回的内容必须严格遵守规范，规范为{cls.RES_LIST}；请看以下文本，识别{recognize_item}类型：
        #             {input};以上文本中是否包含以下{item_type_name}列表中的事件类型，{item_type_name}列表为{item_type};
        #             返回格式要求：如果包含则返回事件类型列表，例如{item_type_name}列表为{example}，如果都包含则返回{all_include_response_example};如果都不包含则返回空列表:[];范围不得超过event_type列表，文本中最有可能包含event_type列表中的哪个事件，只给列表，不要废话, 双引号包字符串。Ensure the response can be parsed by Python json.loads."""
        # print(prompt)
        # print(recognize_item)
        # print(item_type)
        # print(item_type_name)
        # print(example)
        prompt = f"Read the TEXT below,and recognize {recognize_item} in the {item_type_name} List.\n" \
                 f"TEXT：\n{input}\n\n"\
                 f"{item_type_name} List：\n{item_type}\n\n"\
                 f"Every {item_type_name} exists in text must return in response.\n" \
                 f"You should only respond in JSON format LIST, which must be a subset list of the {item_type_name} list.\n"\
                 f"If there is no {item_type_name} in the text, return []\n" \
                 f"Return {item_type_name} as many as possible.\n"\
                 f"Ensure the response can be parsed by Python json.loads"
#                 f"如果包含则返回{recognize_item}类型列表，例如{item_type_name}列表为{example}，如果都包含则返回{all_include_response_example}\n"\

        return cls._get_message_extract(prompt)
    
    @classmethod
    def _get_extraction_tag_by_type(cls,item_type,input,info):
        return cls._assemble_item_type_prompt(item_type,input,*info)
    
    @classmethod
    def _assemble_event_extraction_prompt(cls,event_json,input_text,example_pairs):
        prompt = f""" 你返回的内容必须严格遵守规范，规范为{cls.RES_JSON}；图谱事件类描述如下:{event_json}；抽取文本中的对应的事件并填充论元的值，没有的则填空;文本为：{input_text};用报文返回，例如事件描述为{example_pairs[0]},返回为：{example_pairs[1]},不要有其他内容。"""
        return cls._get_message_extract(prompt)

    @classmethod
    def _assemble_entity_extraction_prompt(cls,event_json,input_text,example_pairs):
        # prompt = f"""
        #             你返回的内容必须严格遵守规范，规范为{cls.RES_LIST}；图谱实体类描述如下:{event_json}；抽取文本中的对应的实体，没有的则填空;文本为：{input_text};用列表返回，例如实体描述为{example_pairs[0]},返回为：{example_pairs[1]},不要有其他内容。"""

        prompt = f"""Read the text below, and extract the entities from text.
                Text:
                {input_text}
                
                Entities to be extracted describe as below:
                {event_json}
                
                You should only respond in JSON format LIST, every element in LIST must be formatted as described below:
                {example_pairs}
                
                If there is no Entity {list(event_json.keys())[0]} in the text, return [].
                Ensure the response can be parsed by Python json.loads
                """
        #                The entity extracted must be the type {list(event_json.keys())[0]}.

        return cls._get_message_extract(prompt)

    @classmethod
    def _assemble_multi_entity_extraction_prompt(cls, event_jsons, input_text, example_pairs):
        # prompt = f"""
        #             你返回的内容必须严格遵守规范，规范为{cls.RES_LIST}；图谱实体类描述如下:{event_json}；抽取文本中的对应的实体，没有的则填空;文本为：{input_text};用列表返回，例如实体描述为{example_pairs[0]},返回为：{example_pairs[1]},不要有其他内容。"""

        prompt = f"""Read the text below, and extract the entities from text.
                    Text:
                    {input_text}

                    Entities to be extracted describe as below:
                    {event_jsons}
                    Ensure all entities of one entity type in every sentence are extracted.
                    You should only respond in JSON format LIST, every entity in LIST must be formatted as described in list below:
                    {example_pairs}
                    
                    If there is no Entity in the text, return [].
                    Ensure the response can be parsed by Python json.loads
                    """
# If can't extract entity text,leave the extracted text as "".
        return cls._get_message_extract(prompt)

    @classmethod
    def _assemble_relation_extraction_prompt(cls,event_json,input_text,example_pairs):
        # prompt = f"""
        #             你返回的内容必须严格遵守规范，规范为{cls.RES_JSON}；图谱关系类描述如下:{event_json}；抽取文本中的对应的关系并填充首尾实体的值，没有的则填空;文本为：{input_text};用报文返回，例如关系描述为{example_pairs[0]},返回为：{example_pairs[1]},不要有其他内容。"""

        prompt = f"""Read the text below, and extract the triple (subject, relation, object) from text.
        Text:
        {input_text}
        
        Triple to be extracted describe as below:
        {event_json}
        
        You should only respond in JSON format LIST, every element in LIST must be formatted as described below:
        {example_pairs}
        
        If the subject or object contains several entities, you must separate them into different triples.
        If can't extract subject or object,leave the extracted text as "".
        If there is no Relation {list(event_json.keys())[0]} in the text, return [].
        Ensure the response can be parsed by Python json.loads
        """
        # prompt = f"""根据文本抽取spo三元组, 三元组类型为s:{企业}，p:{生产产品}，o:{产品}；文本为：{input_text}"""

        return cls._get_message_extract(prompt)

    @classmethod
    def _assemble_multi_relation_extraction_prompt(cls, event_jsons, input_text, example_pairs):
        # prompt = f"""
        #             你返回的内容必须严格遵守规范，规范为{cls.RES_JSON}；图谱关系类描述如下:{event_json}；抽取文本中的对应的关系并填充首尾实体的值，没有的则填空;文本为：{input_text};用报文返回，例如关系描述为{example_pairs[0]},返回为：{example_pairs[1]},不要有其他内容。"""
        # prompt = f"""
        # 根据文本抽取spo三元组, 三元组类型为
        # s:企业，p:成立时间，o:时间
        # s:企业，p:公司地址，o:地址
        # s:企业，p:生产产品，o:产品
        # s:企业，p:获得荣誉，o:荣誉
        # 文本：{input_text}
        # """
        event_type = list(event_jsons[0].keys())[0]
        subj_type = event_jsons[0][event_type]['subject']['type']
        obj_type = event_jsons[0][event_type]['object']['type']

        prompt = f"""Read the text below, and extract the triples (subject, relation, object) from text.
            Text:
            {input_text}

            Triples and the description of subject and object to be extracted describe as below:
            {event_jsons}
            Ensure all triples of each triple type above in every sentence are extracted.
            You should only respond in JSON format LIST, every element in LIST must be formatted as described in list below:
            {example_pairs}
            If the subject text or object text contains several entities, you must separate them into different triples.
            If can't extract subject or object,leave the extracted text as "".
            If can't extract the requested triples from the text, return [].
            Ensure the response can be parsed by Python json.loads
            """
        # prompt = f"""根据文本抽取spo三元组, 三元组类型为s:{企业}，p:{生产产品}，o:{产品}；文本为：{input_text}"""

        return cls._get_message_extract(prompt)

    @classmethod
    def get_extraction_tag_prompt(cls, input, type, item_type):
        if type == "entity":
            info = PromptTemplate.get_entity_tag_template()
            return cls._get_extraction_tag_by_type(item_type=item_type[0], input=input, info=info)
        if type == "event":
            info = PromptTemplate.get_event_tag_template()
            return cls._get_extraction_tag_by_type(item_type=item_type[1], input=input, info=info)
        if type == "relation":
            info = PromptTemplate.get_relation_tag_template()
            return cls._get_extraction_tag_by_type(item_type=item_type[2], input=input, info=info)
        return None

    @classmethod
    def get_extraction_prompt(cls,event_json,input_text, ext_type):
        if ext_type == 'event':
            info = PromptTemplate.get_event_extraction_template()
            return cls._assemble_event_extraction_prompt(event_json=event_json,input_text=input_text, example_pairs=info)

        elif ext_type == 'entity':
            # info = PromptTemplate.get_entity_extraction_template()
            ret_formats = []
            if isinstance(event_json, list):
                for ej in event_json:
                    ret_format = PromptTemplate.get_entity_extraction_response_format(ej)
                    ret_format = json.loads(ret_format)
                    ret_formats.append(ret_format)
                ret_formats = json.dumps(ret_formats, ensure_ascii=False, indent=4, separators=[',', ':'])
                return cls._assemble_multi_entity_extraction_prompt(event_json, input_text, ret_formats)

            else:
                ret_format = PromptTemplate.get_entity_extraction_response_format(event_json)
                return cls._assemble_entity_extraction_prompt(event_json=event_json,input_text=input_text,
                                                              example_pairs=ret_format)

        elif ext_type == 'relation':
            # info = PromptTemplate.get_relation_extraction_template()
            ret_formats = []
            new_event_json = []
            if isinstance(event_json, list):
                for ej in event_json:
                    ret_format = PromptTemplate.get_relation_extraction_response_format(ej)
                    ret_format = json.loads(ret_format)
                    ret_formats.append(ret_format)
                    # new_event_json.append(PromptTemplate.proc_relation_type_format(ej))
                ret_formats = json.dumps(ret_formats, ensure_ascii=False, indent=4, separators=[',', ':'])
                # print(new_event_json)
                return cls._assemble_multi_relation_extraction_prompt(event_json, input_text, ret_formats)

            else:
                ret_format = PromptTemplate.get_relation_extraction_response_format(event_json)
                # new_event_json = PromptTemplate.proc_relation_type_format(event_json)
                return cls._assemble_relation_extraction_prompt(event_json=event_json,
                                                                input_text=input_text, example_pairs=ret_format)


    @classmethod
    def _assemble_ops_type_prompt(cls,ops_json,input_text,example_pairs):
        prompt = f"""用户操作知识图谱软件，根据用户问题判断最有可能一个的操作类型，操作类型为{ops_json},用户问题为{input_text},用列表返回;返回范围严格按照操作类型中包含的；如果都不包含则返回空列表:[];那么用户输入包含的操作类型是什么，直接用列表返回给我，不要废话，不要解释，不要说“根据什么，我返回什么”，直接给我list，里面是操作类型, 双引号包字符串。
            """
        return cls._get_message(prompt)

    @classmethod
    def _assemble_canvas_ops_prompt(cls,ops_json,input_text,example_pairs):
        prompt = f"""根据用户问题判断画布操作类型，操作类型为{ops_json},用户问题为{input_text},用列表返回, 返回范围严格按照操作类型中包含的；如果都不包含则返回空列表:[];用户输入包含的操作类型是什么，直接用列表返回给我，不要解释, 双引号包字符串,不要有"根据xxx,返回xxx"的解释。
            """
        return cls._get_message(prompt)
    
    @classmethod
    def get_ops_type_prompt(cls,ops_json,input_text):
        info = PromptTemplate.get_ops_type_template()
        return cls._assemble_ops_type_prompt(ops_json,input_text=input_text, example_pairs=info)

    @classmethod
    def _assemble_qa_ops_prompt(cls,ops_json,input_text,example_pairs):
        # prompt = f"""
        #     根据用户问题判断最有可能执行的操作，操作类型为{ops_json},用户问题为{input_text},用列表返回，例如操作类型为{example_pairs[0]},最有可能是物质物料(化学品）则返回{example_pairs[1]};返回范围严格按照操作类型中包含的；如果都不包含则返回空列表:[];需要执行的操作是什么，给我最精简的回答，只有list，里面是操作类型, 双引号包字符串。
        #     """
        prompt = f"""根据用户问题判断最有可能执行的操作，操作类型为{ops_json},用户问题为{input_text},用列表返回;返回范围严格按照操作类型中包含的；如果都不包含则返回空列表:[];需要执行的操作是什么，给我最精简的回答，只有list，里面是英文的操作类型，最终答案必须为"['xxx']"形式。
            """
        # prompt = f"""根据用户输入问题，判断所要执行的操作。可能执行的操作有以下几种，操作名称是字典的key：{ops_json}。用户问题：{input_text}，如果判断出问题所对应的操作，直接以列表返回<>表示的操作名称；否则，返回[]。比如，['<competitive_enterprise>']。直接返回操作名称即可，不要有列表以外的其他内容"""
        return cls._get_message(prompt)

    @classmethod
    def get_qa_ops_prompt(cls,ops_json,input_text):
        info = PromptTemplate.get_qa_ops_template()
        return cls._assemble_qa_ops_prompt(ops_json,input_text=input_text, example_pairs=info)

    @classmethod
    def _assemble_qa_slot_prompt(cls,slot_list,input_text,example_pairs):
        prompt = f"""抽取query中的槽值，填充slot_value：你返回的内容必须严格遵守规范，规范为{cls.RES_LIST}；query为{input_text},槽位列表为{slot_list},用列表返回；例如query为{example_pairs[1]},返回为：{example_pairs[2]},范围不能超过槽位列表{slot_list}，只填充slot_value,不许改变其他字段，如果query里没有则不填充，返回[]列表，不要有列表以外的其他解释, 双引号包字符串。
            """
        return cls._get_message(prompt)

    @classmethod
    def get_qa_slot_prompt(cls, query, slot_list):
        info = PromptTemplate.get_qa_slot_template()
        return cls._assemble_qa_slot_prompt(slot_list,input_text=query, example_pairs=info)

    @classmethod
    def get_qa_answer_explain_prompt(cls,query, res_schema):
        # format="""{"answer":"xxx[<1>]xxx,xxx[<2>]...","reference":[{"[<1>]":{"vid":"xxx","name":"entity_name1"},{"[<2>]":{"vid":"xxx","name":"entity_name2"}...}"""
        # prompt = f"""
        #     请严格按照json报文回复：请根据图谱数据：{res_schema},回答{query},放在回复报文的"answer"字段里，在answer里出现的实体字符串全部替换(replace)为[<1>],[<2>]...等标签，被替换的实体放在name字段里,不要出现重复名称的实体，并返回报文包含标签与vid的映射，报文格式为：{format}，答案长度限制在500以内。
        #     """
        file_schema = """{[1]: {"name":"xx", "gns": "xxx"}}"""
        # format = """{"answer":"xxx[<1>]xxx,xxx[<2>]...","reference":[{"[<1>]":{"vid":"xxx","name":"entity_name1"},{"[<2>]":{"vid":"xxx","name":"entity_name2"}...}"""
        # prompt = f"""请严格按照json报文回复：请根据图谱数据：{res_schema},图谱数据中entity_list表示实体信息,edge_list表示实体之间的关系。请回答用户问题<{query}>,答案放在报文的"answer"字段里,如果不明确答案直接回复，['很抱歉，没有理解您的问题。']。如果可以分点论述，请按以下格式组织答案:
        # 1、xxx;\n2、xxx等；详细信息请查阅图谱数据。"""
        prompt = task_prompt.get_prompt(query, res_schema, "competitive_enterprise")
        return cls._get_message(prompt)

    @classmethod
    def get_canvas_ops_prompt(cls,ops_json,input_text):
        info = PromptTemplate.get_canvas_ops_type_template()
        return cls._assemble_canvas_ops_prompt(ops_json,input_text=input_text, example_pairs=info)

