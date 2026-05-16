from faker import Faker

fake = Faker("zh_CN")


def meter_data(**overrides):
    return {
        "serial_number": fake.unique.bothify("DLMS####???"),
        "meter_name": fake.word() + "测试表",
        "meter_type_id": 1,
        "project_id": 1,
        "protocol": fake.random_element(["DLMS", "Modbus", "MQTT"]),
        "line_type": fake.random_element(["single_phase", "3P4W", "DC", "3P3W"]),
        "manufacturer": fake.company(),
        "model": fake.bothify("MOD-##??"),
        "firmware_version": f"v{fake.random_int(1,5)}.{fake.random_int(0,9)}.{fake.random_int(0,9)}",
        "hardware_version": f"v{fake.random_int(1,3)}.0",
        "frame_number": fake.bothify("??-##"),
        "location": f"实验室{fake.random_int(1,10)}区",
        "notes": fake.sentence(),
        **overrides,
    }


def user_data(**overrides):
    return {
        "username": fake.unique.user_name(),
        "password": "Test123456!",
        "name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "department_id": 1,
        "role_ids": [3],
        **overrides,
    }


def task_data(**overrides):
    return {
        "task_name": fake.sentence(nb_words=4),
        "task_type": fake.random_element(["cron", "interval", "once"]),
        "schedule_config": {"interval": 120, "unit": "seconds"},
        "execution_content": {
            "action": "read",
            "points": ["1.0.0.0.0.255", "1.0.1.8.0.255"],
        },
        "filter_config": {"project_id": 1},
        "priority": fake.random_int(1, 10),
        "retry_times": 3,
        "timeout": 300,
        "is_enabled": True,
        **overrides,
    }


def project_data(**overrides):
    return {
        "name": fake.company() + "项目",
        "description": fake.sentence(),
        "test_lead_id": 1,
        "dev_lead_id": 1,
        "start_date": fake.date_this_year().isoformat(),
        "end_date": fake.date_this_year(after_today=True).isoformat(),
        **overrides,
    }
