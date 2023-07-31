CREATE TABLE transponders (
	id INT NOT NULL AUTO_INCREMENT,
	sat_number INT,
	delivery_system varchar(10),
	lnb varchar(25),
	frequency BIGINT,
	polarization varchar(10),
	symbol_rate BIGINT,
	modulation varchar(10),
	pilot varchar(10),
	inner_fec varchar(10),
	inversion varchar(25),
	rolloff varchar(10),
	stream_id INT,
	weight INT,
	last_scanned datetime,
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX transponders_id ON transponders (sat_number, frequency, polarization, symbol_rate, stream_id);

CREATE TABLE transponder_stats(
	id INT NOT NULL AUTO_INCREMENT,
	transponder INT,
	result INT,
	duration double,
	time datetime,
	PRIMARY KEY (id)
);

CREATE INDEX transponder on transponder_stats(transponder);
