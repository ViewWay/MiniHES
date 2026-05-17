--
-- PostgreSQL database dump
--

\restrict 9bhpoHlXGOUTlm2WvXyIGBj8mxfePseOcE28ZxQby2aZXrxP9fPK8IQO7M182YC

-- Dumped from database version 18.3 (Homebrew)
-- Dumped by pg_dump version 18.3 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: col_data_quality; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.col_data_quality (
    id integer NOT NULL,
    meter_id integer NOT NULL,
    task_id integer,
    stat_date date NOT NULL,
    total_points integer NOT NULL,
    success_points integer NOT NULL,
    failed_points integer NOT NULL,
    quality_score numeric(5,2),
    abnormal_count integer NOT NULL,
    first_collect_time timestamp with time zone,
    last_collect_time timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE col_data_quality; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.col_data_quality IS '数据质量统计表';


--
-- Name: col_data_quality_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.col_data_quality_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: col_data_quality_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.col_data_quality_id_seq OWNED BY public.col_data_quality.id;


--
-- Name: col_meter_reading; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.col_meter_reading (
    id integer NOT NULL,
    meter_id integer NOT NULL,
    point_id integer NOT NULL,
    task_id integer,
    reading_value numeric(18,6) NOT NULL,
    reading_time timestamp with time zone NOT NULL,
    quality character varying(20) NOT NULL,
    source character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE col_meter_reading; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.col_meter_reading IS '抄表读数记录表';


--
-- Name: col_meter_reading_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.col_meter_reading_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: col_meter_reading_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.col_meter_reading_id_seq OWNED BY public.col_meter_reading.id;


--
-- Name: col_reading_daily; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.col_reading_daily (
    id integer NOT NULL,
    meter_id integer NOT NULL,
    point_id integer NOT NULL,
    stat_date date NOT NULL,
    min_value numeric(18,6) NOT NULL,
    max_value numeric(18,6) NOT NULL,
    avg_value numeric(18,6) NOT NULL,
    first_value numeric(18,6) NOT NULL,
    last_value numeric(18,6) NOT NULL,
    reading_count integer NOT NULL,
    delta numeric(18,6),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE col_reading_daily; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.col_reading_daily IS '日统计汇总表';


--
-- Name: col_reading_daily_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.col_reading_daily_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: col_reading_daily_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.col_reading_daily_id_seq OWNED BY public.col_reading_daily.id;


--
-- Name: col_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.col_session (
    id integer NOT NULL,
    meter_id integer NOT NULL,
    project_id integer,
    task_id integer,
    mongo_db character varying(200) NOT NULL,
    mongo_collection character varying(200) NOT NULL,
    mongo_doc_id character varying(100) NOT NULL,
    source character varying(20) NOT NULL,
    source_file character varying(500) NOT NULL,
    started_at timestamp with time zone,
    finished_at timestamp with time zone,
    duration_ms integer NOT NULL,
    status character varying(20) NOT NULL,
    total_read integer NOT NULL,
    total_success integer NOT NULL,
    total_failed integer NOT NULL,
    sheet_count integer NOT NULL,
    connection_type character varying(20) NOT NULL,
    communication character varying(20) NOT NULL,
    meter_ip character varying(50) NOT NULL,
    ping_status boolean NOT NULL,
    error_summary text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE col_session; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.col_session IS '采集会话表（PG-MongoDB 桥梁）';


--
-- Name: col_session_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.col_session_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: col_session_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.col_session_id_seq OWNED BY public.col_session.id;


--
-- Name: col_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.col_task (
    id integer NOT NULL,
    task_name character varying(100) NOT NULL,
    task_type character varying(20) NOT NULL,
    schedule_config json NOT NULL,
    execution_content json NOT NULL,
    filter_config json NOT NULL,
    priority integer NOT NULL,
    retry_times integer NOT NULL,
    timeout integer NOT NULL,
    is_enabled boolean NOT NULL,
    last_execute_time timestamp with time zone,
    next_execute_time timestamp with time zone,
    created_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE col_task; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.col_task IS '采集任务表';


--
-- Name: col_task_device; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.col_task_device (
    id integer NOT NULL,
    log_id integer NOT NULL,
    task_id integer NOT NULL,
    meter_id integer NOT NULL,
    status character varying(20) NOT NULL,
    retry_count integer NOT NULL,
    error_code character varying(50) NOT NULL,
    error_message text,
    start_time timestamp with time zone,
    end_time timestamp with time zone,
    duration_ms integer NOT NULL,
    data_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE col_task_device; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.col_task_device IS '任务设备执行明细表';


--
-- Name: col_task_device_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.col_task_device_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: col_task_device_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.col_task_device_id_seq OWNED BY public.col_task_device.id;


--
-- Name: col_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.col_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: col_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.col_task_id_seq OWNED BY public.col_task.id;


--
-- Name: col_task_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.col_task_log (
    id integer NOT NULL,
    task_id integer NOT NULL,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone,
    duration_ms integer NOT NULL,
    status character varying(20) NOT NULL,
    total_devices integer NOT NULL,
    success_devices integer NOT NULL,
    failed_devices integer NOT NULL,
    error_message text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE col_task_log; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.col_task_log IS '任务执行日志表';


--
-- Name: col_task_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.col_task_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: col_task_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.col_task_log_id_seq OWNED BY public.col_task_log.id;


--
-- Name: dev_meter; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_meter (
    id integer NOT NULL,
    serial_number character varying(50) NOT NULL,
    meter_name character varying(100) NOT NULL,
    meter_type_id integer,
    project_id integer,
    protocol character varying(20) NOT NULL,
    line_type character varying(20) NOT NULL,
    manufacturer character varying(100) NOT NULL,
    model character varying(100) NOT NULL,
    firmware_version character varying(50) NOT NULL,
    hardware_version character varying(50) NOT NULL,
    frame_number character varying(50) NOT NULL,
    location character varying(200) NOT NULL,
    current_status character varying(20) NOT NULL,
    factory_date date,
    purchase_date date,
    warranty_date date,
    notes text NOT NULL,
    created_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE dev_meter; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dev_meter IS '电表设备表';


--
-- Name: dev_meter_attachment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_meter_attachment (
    id integer NOT NULL,
    meter_id integer NOT NULL,
    filename character varying(200) NOT NULL,
    file_path character varying(500) NOT NULL,
    size integer NOT NULL,
    uploaded_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE dev_meter_attachment; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dev_meter_attachment IS '电表附件表';


--
-- Name: dev_meter_attachment_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_meter_attachment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_meter_attachment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_meter_attachment_id_seq OWNED BY public.dev_meter_attachment.id;


--
-- Name: dev_meter_borrow; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_meter_borrow (
    id integer NOT NULL,
    meter_id integer NOT NULL,
    borrower_id integer,
    borrow_reason character varying(200) NOT NULL,
    expected_return_date date,
    actual_return_date date,
    dept_approver_id integer,
    lab_approver_id integer,
    approval_status character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE dev_meter_borrow; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dev_meter_borrow IS '电表借还记录表';


--
-- Name: dev_meter_borrow_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_meter_borrow_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_meter_borrow_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_meter_borrow_id_seq OWNED BY public.dev_meter_borrow.id;


--
-- Name: dev_meter_comm; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_meter_comm (
    id integer NOT NULL,
    meter_id integer NOT NULL,
    protocol character varying(20) NOT NULL,
    connection_type character varying(20) NOT NULL,
    host character varying(255) NOT NULL,
    port integer NOT NULL,
    device_address character varying(50) NOT NULL,
    baud_rate integer NOT NULL,
    parity character varying(10) NOT NULL,
    data_bits integer NOT NULL,
    stop_bits integer NOT NULL,
    auth_config json,
    timeout integer NOT NULL,
    retry_times integer NOT NULL,
    is_enabled boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE dev_meter_comm; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dev_meter_comm IS '电表通信配置表';


--
-- Name: dev_meter_comm_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_meter_comm_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_meter_comm_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_meter_comm_id_seq OWNED BY public.dev_meter_comm.id;


--
-- Name: dev_meter_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_meter_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_meter_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_meter_id_seq OWNED BY public.dev_meter.id;


--
-- Name: dev_meter_point; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_meter_point (
    id integer NOT NULL,
    meter_id integer NOT NULL,
    obis_code character varying(30) NOT NULL,
    class_id integer NOT NULL,
    attribute_id integer NOT NULL,
    point_name character varying(100) NOT NULL,
    module character varying(50) NOT NULL,
    point_type character varying(50) NOT NULL,
    data_type character varying(20) NOT NULL,
    unit character varying(20) NOT NULL,
    scaler integer NOT NULL,
    is_collectible boolean NOT NULL,
    description text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE dev_meter_point; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dev_meter_point IS '测量点定义表';


--
-- Name: dev_meter_point_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_meter_point_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_meter_point_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_meter_point_id_seq OWNED BY public.dev_meter_point.id;


--
-- Name: dev_meter_repair; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_meter_repair (
    id integer NOT NULL,
    meter_id integer NOT NULL,
    description text NOT NULL,
    cost numeric(12,2) NOT NULL,
    status character varying(20) NOT NULL,
    repaired_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE dev_meter_repair; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dev_meter_repair IS '电表维修记录表';


--
-- Name: dev_meter_repair_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_meter_repair_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_meter_repair_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_meter_repair_id_seq OWNED BY public.dev_meter_repair.id;


--
-- Name: dev_meter_snapshot; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_meter_snapshot (
    id integer NOT NULL,
    meter_id integer NOT NULL,
    online_status boolean NOT NULL,
    last_comm_time timestamp with time zone,
    signal_strength integer,
    firmware_version character varying(50) NOT NULL,
    error_code character varying(20) NOT NULL,
    stack_usage integer,
    eeprom_write_count integer,
    last_data_time timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE dev_meter_snapshot; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dev_meter_snapshot IS '电表实时快照表';


--
-- Name: dev_meter_snapshot_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_meter_snapshot_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_meter_snapshot_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_meter_snapshot_id_seq OWNED BY public.dev_meter_snapshot.id;


--
-- Name: dev_meter_status; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_meter_status (
    id integer NOT NULL,
    meter_id integer NOT NULL,
    old_status character varying(20) NOT NULL,
    new_status character varying(20) NOT NULL,
    reason character varying(200) NOT NULL,
    changed_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE dev_meter_status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dev_meter_status IS '电表状态变更记录表';


--
-- Name: dev_meter_status_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_meter_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_meter_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_meter_status_id_seq OWNED BY public.dev_meter_status.id;


--
-- Name: dev_meter_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_meter_type (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(50) NOT NULL,
    description text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE dev_meter_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dev_meter_type IS '电表类型表';


--
-- Name: dev_meter_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_meter_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_meter_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_meter_type_id_seq OWNED BY public.dev_meter_type.id;


--
-- Name: dev_project; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_project (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    description text NOT NULL,
    test_lead_id integer,
    dev_lead_id integer,
    start_date date,
    end_date date,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE dev_project; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dev_project IS '项目表';


--
-- Name: dev_project_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_project_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_project_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_project_id_seq OWNED BY public.dev_project.id;


--
-- Name: dev_wire_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dev_wire_type (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(50) NOT NULL,
    description text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE dev_wire_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.dev_wire_type IS '接线方式表';


--
-- Name: dev_wire_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dev_wire_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dev_wire_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dev_wire_type_id_seq OWNED BY public.dev_wire_type.id;


--
-- Name: lab_defect; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lab_defect (
    id integer NOT NULL,
    test_id integer NOT NULL,
    title character varying(200) NOT NULL,
    description text NOT NULL,
    severity character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    meter_id integer,
    detected_at timestamp with time zone,
    resolved_by integer,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE lab_defect; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.lab_defect IS '缺陷记录表';


--
-- Name: lab_defect_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lab_defect_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lab_defect_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lab_defect_id_seq OWNED BY public.lab_defect.id;


--
-- Name: lab_test_report; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lab_test_report (
    id integer NOT NULL,
    test_id integer NOT NULL,
    report_number character varying(50) NOT NULL,
    test_type character varying(50) NOT NULL,
    test_environment character varying(200) NOT NULL,
    test_duration_days integer NOT NULL,
    firmware_version character varying(50) NOT NULL,
    hardware_version character varying(50) NOT NULL,
    conclusion character varying(20) NOT NULL,
    notes text NOT NULL,
    generated_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE lab_test_report; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.lab_test_report IS '测试报告表';


--
-- Name: lab_test_report_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lab_test_report_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lab_test_report_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lab_test_report_id_seq OWNED BY public.lab_test_report.id;


--
-- Name: lab_test_task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lab_test_task (
    id integer NOT NULL,
    test_name character varying(100) NOT NULL,
    test_type character varying(50) NOT NULL,
    project_id integer,
    status character varying(20) NOT NULL,
    description text NOT NULL,
    start_time timestamp with time zone,
    expected_end_time timestamp with time zone,
    created_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE lab_test_task; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.lab_test_task IS '测试任务表';


--
-- Name: lab_test_task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lab_test_task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lab_test_task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lab_test_task_id_seq OWNED BY public.lab_test_task.id;


--
-- Name: sys_alarm_record; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sys_alarm_record (
    id integer NOT NULL,
    meter_id integer NOT NULL,
    rule_id integer,
    alarm_type character varying(50) NOT NULL,
    severity character varying(20) NOT NULL,
    alarm_message text NOT NULL,
    alarm_value numeric(20,6),
    threshold_value numeric(20,6),
    is_handled boolean NOT NULL,
    handled_by integer,
    handled_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE sys_alarm_record; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sys_alarm_record IS '告警记录表';


--
-- Name: sys_alarm_record_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sys_alarm_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sys_alarm_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sys_alarm_record_id_seq OWNED BY public.sys_alarm_record.id;


--
-- Name: sys_alarm_rule; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sys_alarm_rule (
    id integer NOT NULL,
    rule_name character varying(100) NOT NULL,
    rule_type character varying(50) NOT NULL,
    point_code character varying(50) NOT NULL,
    condition_config json,
    severity character varying(20) NOT NULL,
    is_enabled boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE sys_alarm_rule; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sys_alarm_rule IS '告警规则表';


--
-- Name: sys_alarm_rule_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sys_alarm_rule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sys_alarm_rule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sys_alarm_rule_id_seq OWNED BY public.sys_alarm_rule.id;


--
-- Name: sys_audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sys_audit_log (
    id integer NOT NULL,
    user_id integer NOT NULL,
    username character varying(50) NOT NULL,
    operation_type character varying(50) NOT NULL,
    resource_type character varying(50) NOT NULL,
    resource_id integer NOT NULL,
    old_values json,
    new_values json,
    ip_address character varying(50) NOT NULL,
    user_agent character varying(500) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE sys_audit_log; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sys_audit_log IS '操作审计日志表';


--
-- Name: sys_audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sys_audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sys_audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sys_audit_log_id_seq OWNED BY public.sys_audit_log.id;


--
-- Name: sys_data_archive; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sys_data_archive (
    id integer NOT NULL,
    archive_type character varying(20) NOT NULL,
    table_name character varying(100) NOT NULL,
    start_time timestamp with time zone NOT NULL,
    end_time timestamp with time zone NOT NULL,
    record_count integer NOT NULL,
    archive_status character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE sys_data_archive; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sys_data_archive IS '数据归档记录表';


--
-- Name: sys_data_archive_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sys_data_archive_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sys_data_archive_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sys_data_archive_id_seq OWNED BY public.sys_data_archive.id;


--
-- Name: sys_department; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sys_department (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(50) NOT NULL,
    parent_id integer,
    sort_order integer NOT NULL,
    leader character varying(50) NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE sys_department; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sys_department IS '部门表';


--
-- Name: sys_department_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sys_department_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sys_department_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sys_department_id_seq OWNED BY public.sys_department.id;


--
-- Name: sys_permission; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sys_permission (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    code character varying(100) NOT NULL,
    type character varying(20) NOT NULL,
    parent_id integer,
    path character varying(200) NOT NULL,
    icon character varying(100) NOT NULL,
    sort_order integer NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE sys_permission; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sys_permission IS '权限表';


--
-- Name: sys_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sys_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sys_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sys_permission_id_seq OWNED BY public.sys_permission.id;


--
-- Name: sys_role; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sys_role (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    code character varying(50) NOT NULL,
    description text NOT NULL,
    sort_order integer NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE sys_role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sys_role IS '角色表';


--
-- Name: sys_role_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sys_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sys_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sys_role_id_seq OWNED BY public.sys_role.id;


--
-- Name: sys_role_permission; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sys_role_permission (
    id integer NOT NULL,
    role_id integer NOT NULL,
    permission_id integer NOT NULL
);


--
-- Name: TABLE sys_role_permission; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sys_role_permission IS '角色权限关联表';


--
-- Name: sys_role_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sys_role_permission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sys_role_permission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sys_role_permission_id_seq OWNED BY public.sys_role_permission.id;


--
-- Name: sys_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sys_user (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(255) NOT NULL,
    name character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    phone character varying(20) NOT NULL,
    avatar character varying(500) NOT NULL,
    department_id integer,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: TABLE sys_user; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sys_user IS '用户表';


--
-- Name: sys_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sys_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sys_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sys_user_id_seq OWNED BY public.sys_user.id;


--
-- Name: sys_user_role; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sys_user_role (
    id integer NOT NULL,
    user_id integer NOT NULL,
    role_id integer NOT NULL
);


--
-- Name: TABLE sys_user_role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sys_user_role IS '用户角色关联表';


--
-- Name: sys_user_role_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sys_user_role_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sys_user_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sys_user_role_id_seq OWNED BY public.sys_user_role.id;


--
-- Name: col_data_quality id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_data_quality ALTER COLUMN id SET DEFAULT nextval('public.col_data_quality_id_seq'::regclass);


--
-- Name: col_meter_reading id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_meter_reading ALTER COLUMN id SET DEFAULT nextval('public.col_meter_reading_id_seq'::regclass);


--
-- Name: col_reading_daily id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_reading_daily ALTER COLUMN id SET DEFAULT nextval('public.col_reading_daily_id_seq'::regclass);


--
-- Name: col_session id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_session ALTER COLUMN id SET DEFAULT nextval('public.col_session_id_seq'::regclass);


--
-- Name: col_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_task ALTER COLUMN id SET DEFAULT nextval('public.col_task_id_seq'::regclass);


--
-- Name: col_task_device id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_task_device ALTER COLUMN id SET DEFAULT nextval('public.col_task_device_id_seq'::regclass);


--
-- Name: col_task_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_task_log ALTER COLUMN id SET DEFAULT nextval('public.col_task_log_id_seq'::regclass);


--
-- Name: dev_meter id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter ALTER COLUMN id SET DEFAULT nextval('public.dev_meter_id_seq'::regclass);


--
-- Name: dev_meter_attachment id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_attachment ALTER COLUMN id SET DEFAULT nextval('public.dev_meter_attachment_id_seq'::regclass);


--
-- Name: dev_meter_borrow id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_borrow ALTER COLUMN id SET DEFAULT nextval('public.dev_meter_borrow_id_seq'::regclass);


--
-- Name: dev_meter_comm id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_comm ALTER COLUMN id SET DEFAULT nextval('public.dev_meter_comm_id_seq'::regclass);


--
-- Name: dev_meter_point id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_point ALTER COLUMN id SET DEFAULT nextval('public.dev_meter_point_id_seq'::regclass);


--
-- Name: dev_meter_repair id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_repair ALTER COLUMN id SET DEFAULT nextval('public.dev_meter_repair_id_seq'::regclass);


--
-- Name: dev_meter_snapshot id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_snapshot ALTER COLUMN id SET DEFAULT nextval('public.dev_meter_snapshot_id_seq'::regclass);


--
-- Name: dev_meter_status id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_status ALTER COLUMN id SET DEFAULT nextval('public.dev_meter_status_id_seq'::regclass);


--
-- Name: dev_meter_type id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_type ALTER COLUMN id SET DEFAULT nextval('public.dev_meter_type_id_seq'::regclass);


--
-- Name: dev_project id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_project ALTER COLUMN id SET DEFAULT nextval('public.dev_project_id_seq'::regclass);


--
-- Name: dev_wire_type id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_wire_type ALTER COLUMN id SET DEFAULT nextval('public.dev_wire_type_id_seq'::regclass);


--
-- Name: lab_defect id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_defect ALTER COLUMN id SET DEFAULT nextval('public.lab_defect_id_seq'::regclass);


--
-- Name: lab_test_report id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_test_report ALTER COLUMN id SET DEFAULT nextval('public.lab_test_report_id_seq'::regclass);


--
-- Name: lab_test_task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_test_task ALTER COLUMN id SET DEFAULT nextval('public.lab_test_task_id_seq'::regclass);


--
-- Name: sys_alarm_record id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_alarm_record ALTER COLUMN id SET DEFAULT nextval('public.sys_alarm_record_id_seq'::regclass);


--
-- Name: sys_alarm_rule id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_alarm_rule ALTER COLUMN id SET DEFAULT nextval('public.sys_alarm_rule_id_seq'::regclass);


--
-- Name: sys_audit_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_audit_log ALTER COLUMN id SET DEFAULT nextval('public.sys_audit_log_id_seq'::regclass);


--
-- Name: sys_data_archive id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_data_archive ALTER COLUMN id SET DEFAULT nextval('public.sys_data_archive_id_seq'::regclass);


--
-- Name: sys_department id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_department ALTER COLUMN id SET DEFAULT nextval('public.sys_department_id_seq'::regclass);


--
-- Name: sys_permission id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_permission ALTER COLUMN id SET DEFAULT nextval('public.sys_permission_id_seq'::regclass);


--
-- Name: sys_role id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_role ALTER COLUMN id SET DEFAULT nextval('public.sys_role_id_seq'::regclass);


--
-- Name: sys_role_permission id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_role_permission ALTER COLUMN id SET DEFAULT nextval('public.sys_role_permission_id_seq'::regclass);


--
-- Name: sys_user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_user ALTER COLUMN id SET DEFAULT nextval('public.sys_user_id_seq'::regclass);


--
-- Name: sys_user_role id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_user_role ALTER COLUMN id SET DEFAULT nextval('public.sys_user_role_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: col_data_quality col_data_quality_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_data_quality
    ADD CONSTRAINT col_data_quality_pkey PRIMARY KEY (id);


--
-- Name: col_meter_reading col_meter_reading_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_meter_reading
    ADD CONSTRAINT col_meter_reading_pkey PRIMARY KEY (id);


--
-- Name: col_reading_daily col_reading_daily_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_reading_daily
    ADD CONSTRAINT col_reading_daily_pkey PRIMARY KEY (id);


--
-- Name: col_session col_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_session
    ADD CONSTRAINT col_session_pkey PRIMARY KEY (id);


--
-- Name: col_task_device col_task_device_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_task_device
    ADD CONSTRAINT col_task_device_pkey PRIMARY KEY (id);


--
-- Name: col_task_log col_task_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_task_log
    ADD CONSTRAINT col_task_log_pkey PRIMARY KEY (id);


--
-- Name: col_task col_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_task
    ADD CONSTRAINT col_task_pkey PRIMARY KEY (id);


--
-- Name: dev_meter_attachment dev_meter_attachment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_attachment
    ADD CONSTRAINT dev_meter_attachment_pkey PRIMARY KEY (id);


--
-- Name: dev_meter_borrow dev_meter_borrow_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_borrow
    ADD CONSTRAINT dev_meter_borrow_pkey PRIMARY KEY (id);


--
-- Name: dev_meter_comm dev_meter_comm_meter_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_comm
    ADD CONSTRAINT dev_meter_comm_meter_id_key UNIQUE (meter_id);


--
-- Name: dev_meter_comm dev_meter_comm_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_comm
    ADD CONSTRAINT dev_meter_comm_pkey PRIMARY KEY (id);


--
-- Name: dev_meter dev_meter_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter
    ADD CONSTRAINT dev_meter_pkey PRIMARY KEY (id);


--
-- Name: dev_meter_point dev_meter_point_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_point
    ADD CONSTRAINT dev_meter_point_pkey PRIMARY KEY (id);


--
-- Name: dev_meter_repair dev_meter_repair_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_repair
    ADD CONSTRAINT dev_meter_repair_pkey PRIMARY KEY (id);


--
-- Name: dev_meter_snapshot dev_meter_snapshot_meter_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_snapshot
    ADD CONSTRAINT dev_meter_snapshot_meter_id_key UNIQUE (meter_id);


--
-- Name: dev_meter_snapshot dev_meter_snapshot_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_snapshot
    ADD CONSTRAINT dev_meter_snapshot_pkey PRIMARY KEY (id);


--
-- Name: dev_meter_status dev_meter_status_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_status
    ADD CONSTRAINT dev_meter_status_pkey PRIMARY KEY (id);


--
-- Name: dev_meter_type dev_meter_type_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_type
    ADD CONSTRAINT dev_meter_type_code_key UNIQUE (code);


--
-- Name: dev_meter_type dev_meter_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_type
    ADD CONSTRAINT dev_meter_type_pkey PRIMARY KEY (id);


--
-- Name: dev_project dev_project_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_project
    ADD CONSTRAINT dev_project_name_key UNIQUE (name);


--
-- Name: dev_project dev_project_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_project
    ADD CONSTRAINT dev_project_pkey PRIMARY KEY (id);


--
-- Name: dev_wire_type dev_wire_type_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_wire_type
    ADD CONSTRAINT dev_wire_type_code_key UNIQUE (code);


--
-- Name: dev_wire_type dev_wire_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_wire_type
    ADD CONSTRAINT dev_wire_type_pkey PRIMARY KEY (id);


--
-- Name: lab_defect lab_defect_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_defect
    ADD CONSTRAINT lab_defect_pkey PRIMARY KEY (id);


--
-- Name: lab_test_report lab_test_report_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_test_report
    ADD CONSTRAINT lab_test_report_pkey PRIMARY KEY (id);


--
-- Name: lab_test_report lab_test_report_report_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_test_report
    ADD CONSTRAINT lab_test_report_report_number_key UNIQUE (report_number);


--
-- Name: lab_test_report lab_test_report_test_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_test_report
    ADD CONSTRAINT lab_test_report_test_id_key UNIQUE (test_id);


--
-- Name: lab_test_task lab_test_task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_test_task
    ADD CONSTRAINT lab_test_task_pkey PRIMARY KEY (id);


--
-- Name: sys_alarm_record sys_alarm_record_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_alarm_record
    ADD CONSTRAINT sys_alarm_record_pkey PRIMARY KEY (id);


--
-- Name: sys_alarm_rule sys_alarm_rule_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_alarm_rule
    ADD CONSTRAINT sys_alarm_rule_pkey PRIMARY KEY (id);


--
-- Name: sys_audit_log sys_audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_audit_log
    ADD CONSTRAINT sys_audit_log_pkey PRIMARY KEY (id);


--
-- Name: sys_data_archive sys_data_archive_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_data_archive
    ADD CONSTRAINT sys_data_archive_pkey PRIMARY KEY (id);


--
-- Name: sys_department sys_department_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_department
    ADD CONSTRAINT sys_department_code_key UNIQUE (code);


--
-- Name: sys_department sys_department_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_department
    ADD CONSTRAINT sys_department_pkey PRIMARY KEY (id);


--
-- Name: sys_permission sys_permission_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_permission
    ADD CONSTRAINT sys_permission_code_key UNIQUE (code);


--
-- Name: sys_permission sys_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_permission
    ADD CONSTRAINT sys_permission_pkey PRIMARY KEY (id);


--
-- Name: sys_role sys_role_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_role
    ADD CONSTRAINT sys_role_code_key UNIQUE (code);


--
-- Name: sys_role_permission sys_role_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_role_permission
    ADD CONSTRAINT sys_role_permission_pkey PRIMARY KEY (id);


--
-- Name: sys_role sys_role_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_role
    ADD CONSTRAINT sys_role_pkey PRIMARY KEY (id);


--
-- Name: sys_user sys_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_user
    ADD CONSTRAINT sys_user_pkey PRIMARY KEY (id);


--
-- Name: sys_user_role sys_user_role_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_user_role
    ADD CONSTRAINT sys_user_role_pkey PRIMARY KEY (id);


--
-- Name: col_data_quality uq_data_quality; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_data_quality
    ADD CONSTRAINT uq_data_quality UNIQUE (meter_id, stat_date);


--
-- Name: dev_meter_point uq_meter_point_obis; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_point
    ADD CONSTRAINT uq_meter_point_obis UNIQUE (meter_id, obis_code, attribute_id);


--
-- Name: col_reading_daily uq_reading_daily; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_reading_daily
    ADD CONSTRAINT uq_reading_daily UNIQUE (meter_id, point_id, stat_date);


--
-- Name: sys_role_permission uq_role_permission; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_role_permission
    ADD CONSTRAINT uq_role_permission UNIQUE (role_id, permission_id);


--
-- Name: sys_user_role uq_user_role; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_user_role
    ADD CONSTRAINT uq_user_role UNIQUE (user_id, role_id);


--
-- Name: ix_col_data_quality_meter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_data_quality_meter_id ON public.col_data_quality USING btree (meter_id);


--
-- Name: ix_col_data_quality_stat_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_data_quality_stat_date ON public.col_data_quality USING btree (stat_date);


--
-- Name: ix_col_meter_reading_meter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_meter_reading_meter_id ON public.col_meter_reading USING btree (meter_id);


--
-- Name: ix_col_meter_reading_point_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_meter_reading_point_id ON public.col_meter_reading USING btree (point_id);


--
-- Name: ix_col_meter_reading_reading_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_meter_reading_reading_time ON public.col_meter_reading USING btree (reading_time);


--
-- Name: ix_col_reading_daily_meter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_reading_daily_meter_id ON public.col_reading_daily USING btree (meter_id);


--
-- Name: ix_col_reading_daily_point_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_reading_daily_point_id ON public.col_reading_daily USING btree (point_id);


--
-- Name: ix_col_reading_daily_stat_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_reading_daily_stat_date ON public.col_reading_daily USING btree (stat_date);


--
-- Name: ix_col_session_meter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_session_meter_id ON public.col_session USING btree (meter_id);


--
-- Name: ix_col_session_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_session_status ON public.col_session USING btree (status);


--
-- Name: ix_col_task_device_log_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_task_device_log_id ON public.col_task_device USING btree (log_id);


--
-- Name: ix_col_task_device_meter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_task_device_meter_id ON public.col_task_device USING btree (meter_id);


--
-- Name: ix_col_task_device_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_task_device_task_id ON public.col_task_device USING btree (task_id);


--
-- Name: ix_col_task_log_task_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_task_log_task_id ON public.col_task_log USING btree (task_id);


--
-- Name: ix_col_task_next_execute_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_col_task_next_execute_time ON public.col_task USING btree (next_execute_time);


--
-- Name: ix_dev_meter_attachment_meter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dev_meter_attachment_meter_id ON public.dev_meter_attachment USING btree (meter_id);


--
-- Name: ix_dev_meter_borrow_meter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dev_meter_borrow_meter_id ON public.dev_meter_borrow USING btree (meter_id);


--
-- Name: ix_dev_meter_current_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dev_meter_current_status ON public.dev_meter USING btree (current_status);


--
-- Name: ix_dev_meter_point_meter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dev_meter_point_meter_id ON public.dev_meter_point USING btree (meter_id);


--
-- Name: ix_dev_meter_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dev_meter_project_id ON public.dev_meter USING btree (project_id);


--
-- Name: ix_dev_meter_repair_meter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dev_meter_repair_meter_id ON public.dev_meter_repair USING btree (meter_id);


--
-- Name: ix_dev_meter_serial_number; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_dev_meter_serial_number ON public.dev_meter USING btree (serial_number);


--
-- Name: ix_dev_meter_status_meter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dev_meter_status_meter_id ON public.dev_meter_status USING btree (meter_id);


--
-- Name: ix_lab_defect_test_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_lab_defect_test_id ON public.lab_defect USING btree (test_id);


--
-- Name: ix_reading_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reading_lookup ON public.col_meter_reading USING btree (meter_id, point_id, reading_time);


--
-- Name: ix_session_meter_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_session_meter_time ON public.col_session USING btree (meter_id, started_at);


--
-- Name: ix_session_project_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_session_project_time ON public.col_session USING btree (project_id, started_at);


--
-- Name: ix_sys_alarm_record_is_handled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sys_alarm_record_is_handled ON public.sys_alarm_record USING btree (is_handled);


--
-- Name: ix_sys_alarm_record_meter_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sys_alarm_record_meter_id ON public.sys_alarm_record USING btree (meter_id);


--
-- Name: ix_sys_audit_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sys_audit_log_created_at ON public.sys_audit_log USING btree (created_at);


--
-- Name: ix_sys_audit_log_operation_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sys_audit_log_operation_type ON public.sys_audit_log USING btree (operation_type);


--
-- Name: ix_sys_audit_log_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sys_audit_log_user_id ON public.sys_audit_log USING btree (user_id);


--
-- Name: ix_sys_user_username; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_sys_user_username ON public.sys_user USING btree (username);


--
-- Name: ix_task_schedule; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_task_schedule ON public.col_task USING btree (is_enabled, next_execute_time);


--
-- Name: col_data_quality col_data_quality_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_data_quality
    ADD CONSTRAINT col_data_quality_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id) ON DELETE RESTRICT;


--
-- Name: col_data_quality col_data_quality_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_data_quality
    ADD CONSTRAINT col_data_quality_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.col_task(id) ON DELETE SET NULL;


--
-- Name: col_meter_reading col_meter_reading_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_meter_reading
    ADD CONSTRAINT col_meter_reading_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id) ON DELETE RESTRICT;


--
-- Name: col_meter_reading col_meter_reading_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_meter_reading
    ADD CONSTRAINT col_meter_reading_point_id_fkey FOREIGN KEY (point_id) REFERENCES public.dev_meter_point(id) ON DELETE RESTRICT;


--
-- Name: col_meter_reading col_meter_reading_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_meter_reading
    ADD CONSTRAINT col_meter_reading_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.col_task(id) ON DELETE SET NULL;


--
-- Name: col_reading_daily col_reading_daily_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_reading_daily
    ADD CONSTRAINT col_reading_daily_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id) ON DELETE RESTRICT;


--
-- Name: col_reading_daily col_reading_daily_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_reading_daily
    ADD CONSTRAINT col_reading_daily_point_id_fkey FOREIGN KEY (point_id) REFERENCES public.dev_meter_point(id) ON DELETE RESTRICT;


--
-- Name: col_session col_session_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_session
    ADD CONSTRAINT col_session_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id) ON DELETE RESTRICT;


--
-- Name: col_session col_session_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_session
    ADD CONSTRAINT col_session_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.dev_project(id) ON DELETE SET NULL;


--
-- Name: col_session col_session_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_session
    ADD CONSTRAINT col_session_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.col_task(id) ON DELETE SET NULL;


--
-- Name: col_task col_task_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_task
    ADD CONSTRAINT col_task_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.sys_user(id) ON DELETE SET NULL;


--
-- Name: col_task_device col_task_device_log_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_task_device
    ADD CONSTRAINT col_task_device_log_id_fkey FOREIGN KEY (log_id) REFERENCES public.col_task_log(id) ON DELETE CASCADE;


--
-- Name: col_task_device col_task_device_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_task_device
    ADD CONSTRAINT col_task_device_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id) ON DELETE RESTRICT;


--
-- Name: col_task_device col_task_device_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_task_device
    ADD CONSTRAINT col_task_device_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.col_task(id) ON DELETE CASCADE;


--
-- Name: col_task_log col_task_log_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.col_task_log
    ADD CONSTRAINT col_task_log_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.col_task(id) ON DELETE CASCADE;


--
-- Name: dev_meter_attachment dev_meter_attachment_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_attachment
    ADD CONSTRAINT dev_meter_attachment_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id) ON DELETE CASCADE;


--
-- Name: dev_meter_attachment dev_meter_attachment_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_attachment
    ADD CONSTRAINT dev_meter_attachment_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.sys_user(id) ON DELETE SET NULL;


--
-- Name: dev_meter_borrow dev_meter_borrow_borrower_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_borrow
    ADD CONSTRAINT dev_meter_borrow_borrower_id_fkey FOREIGN KEY (borrower_id) REFERENCES public.sys_user(id) ON DELETE SET NULL;


--
-- Name: dev_meter_borrow dev_meter_borrow_dept_approver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_borrow
    ADD CONSTRAINT dev_meter_borrow_dept_approver_id_fkey FOREIGN KEY (dept_approver_id) REFERENCES public.sys_user(id) ON DELETE SET NULL;


--
-- Name: dev_meter_borrow dev_meter_borrow_lab_approver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_borrow
    ADD CONSTRAINT dev_meter_borrow_lab_approver_id_fkey FOREIGN KEY (lab_approver_id) REFERENCES public.sys_user(id) ON DELETE SET NULL;


--
-- Name: dev_meter_borrow dev_meter_borrow_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_borrow
    ADD CONSTRAINT dev_meter_borrow_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id) ON DELETE RESTRICT;


--
-- Name: dev_meter_comm dev_meter_comm_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_comm
    ADD CONSTRAINT dev_meter_comm_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id) ON DELETE CASCADE;


--
-- Name: dev_meter dev_meter_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter
    ADD CONSTRAINT dev_meter_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.sys_user(id) ON DELETE SET NULL;


--
-- Name: dev_meter dev_meter_meter_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter
    ADD CONSTRAINT dev_meter_meter_type_id_fkey FOREIGN KEY (meter_type_id) REFERENCES public.dev_meter_type(id) ON DELETE SET NULL;


--
-- Name: dev_meter_point dev_meter_point_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_point
    ADD CONSTRAINT dev_meter_point_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id) ON DELETE CASCADE;


--
-- Name: dev_meter dev_meter_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter
    ADD CONSTRAINT dev_meter_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.dev_project(id) ON DELETE SET NULL;


--
-- Name: dev_meter_repair dev_meter_repair_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_repair
    ADD CONSTRAINT dev_meter_repair_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id) ON DELETE RESTRICT;


--
-- Name: dev_meter_repair dev_meter_repair_repaired_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_repair
    ADD CONSTRAINT dev_meter_repair_repaired_by_fkey FOREIGN KEY (repaired_by) REFERENCES public.sys_user(id) ON DELETE SET NULL;


--
-- Name: dev_meter_snapshot dev_meter_snapshot_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_snapshot
    ADD CONSTRAINT dev_meter_snapshot_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id) ON DELETE CASCADE;


--
-- Name: dev_meter_status dev_meter_status_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_status
    ADD CONSTRAINT dev_meter_status_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.sys_user(id) ON DELETE SET NULL;


--
-- Name: dev_meter_status dev_meter_status_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_meter_status
    ADD CONSTRAINT dev_meter_status_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id) ON DELETE CASCADE;


--
-- Name: dev_project dev_project_dev_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_project
    ADD CONSTRAINT dev_project_dev_lead_id_fkey FOREIGN KEY (dev_lead_id) REFERENCES public.sys_user(id);


--
-- Name: dev_project dev_project_test_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dev_project
    ADD CONSTRAINT dev_project_test_lead_id_fkey FOREIGN KEY (test_lead_id) REFERENCES public.sys_user(id);


--
-- Name: lab_defect lab_defect_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_defect
    ADD CONSTRAINT lab_defect_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id);


--
-- Name: lab_defect lab_defect_resolved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_defect
    ADD CONSTRAINT lab_defect_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES public.sys_user(id);


--
-- Name: lab_defect lab_defect_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_defect
    ADD CONSTRAINT lab_defect_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.lab_test_task(id);


--
-- Name: lab_test_report lab_test_report_generated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_test_report
    ADD CONSTRAINT lab_test_report_generated_by_fkey FOREIGN KEY (generated_by) REFERENCES public.sys_user(id);


--
-- Name: lab_test_report lab_test_report_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_test_report
    ADD CONSTRAINT lab_test_report_test_id_fkey FOREIGN KEY (test_id) REFERENCES public.lab_test_task(id);


--
-- Name: lab_test_task lab_test_task_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_test_task
    ADD CONSTRAINT lab_test_task_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.sys_user(id);


--
-- Name: lab_test_task lab_test_task_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_test_task
    ADD CONSTRAINT lab_test_task_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.dev_project(id);


--
-- Name: sys_alarm_record sys_alarm_record_handled_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_alarm_record
    ADD CONSTRAINT sys_alarm_record_handled_by_fkey FOREIGN KEY (handled_by) REFERENCES public.sys_user(id);


--
-- Name: sys_alarm_record sys_alarm_record_meter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_alarm_record
    ADD CONSTRAINT sys_alarm_record_meter_id_fkey FOREIGN KEY (meter_id) REFERENCES public.dev_meter(id);


--
-- Name: sys_alarm_record sys_alarm_record_rule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_alarm_record
    ADD CONSTRAINT sys_alarm_record_rule_id_fkey FOREIGN KEY (rule_id) REFERENCES public.sys_alarm_rule(id);


--
-- Name: sys_audit_log sys_audit_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_audit_log
    ADD CONSTRAINT sys_audit_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.sys_user(id);


--
-- Name: sys_department sys_department_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_department
    ADD CONSTRAINT sys_department_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.sys_department(id);


--
-- Name: sys_permission sys_permission_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_permission
    ADD CONSTRAINT sys_permission_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.sys_permission(id) ON DELETE SET NULL;


--
-- Name: sys_role_permission sys_role_permission_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_role_permission
    ADD CONSTRAINT sys_role_permission_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.sys_permission(id) ON DELETE CASCADE;


--
-- Name: sys_role_permission sys_role_permission_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_role_permission
    ADD CONSTRAINT sys_role_permission_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.sys_role(id) ON DELETE CASCADE;


--
-- Name: sys_user sys_user_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_user
    ADD CONSTRAINT sys_user_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.sys_department(id);


--
-- Name: sys_user_role sys_user_role_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_user_role
    ADD CONSTRAINT sys_user_role_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.sys_role(id) ON DELETE CASCADE;


--
-- Name: sys_user_role sys_user_role_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sys_user_role
    ADD CONSTRAINT sys_user_role_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.sys_user(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 9bhpoHlXGOUTlm2WvXyIGBj8mxfePseOcE28ZxQby2aZXrxP9fPK8IQO7M182YC

