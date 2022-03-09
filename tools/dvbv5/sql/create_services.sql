CREATE TABLE dvb_service (
	id INT NOT NULL AUTO_INCREMENT,
	transponder INT,
	service_name varchar(128),
	service_id INT,
	PRIMARY KEY (id)
);

CREATE INDEX dvb_service_ind_transponder ON dvb_service (transponder);

CREATE TABLE text_service (
	id INT NOT NULL AUTO_INCREMENT,
	transponder INT,
	pid INT,
	service_id INT,
	service_name varchar(128),
	header varchar(42),
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX text_service_ind ON text_service (transponder,pid);
