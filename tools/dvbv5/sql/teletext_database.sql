-- MariaDB dump 10.19  Distrib 10.5.12-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: teletext
-- ------------------------------------------------------
-- Server version	10.5.12-MariaDB-0+deb11u1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `dvb_service`
--

DROP TABLE IF EXISTS `dvb_service`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dvb_service` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `transponder` int(11) DEFAULT NULL,
  `service_name` varchar(128) DEFAULT NULL,
  `service_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `dvb_service_ind_transponder` (`transponder`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dvb_service`
--

LOCK TABLES `dvb_service` WRITE;
/*!40000 ALTER TABLE `dvb_service` DISABLE KEYS */;
/*!40000 ALTER TABLE `dvb_service` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `text_service`
--

DROP TABLE IF EXISTS `text_service`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `text_service` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `transponder` int(11) DEFAULT NULL,
  `pid` int(11) DEFAULT NULL,
  `service_id` int(11) DEFAULT NULL,
  `service_name` varchar(128) DEFAULT NULL,
  `header` varchar(42) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `text_service_ind` (`transponder`,`pid`)
) ENGINE=InnoDB AUTO_INCREMENT=166 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `text_service`
--

LOCK TABLES `text_service` WRITE;
/*!40000 ALTER TABLE `text_service` DISABLE KEYS */;
INSERT INTO `text_service` VALUES (1,10,39,NULL,'de.VOX-up','207 VOX up   Fr 11.Mar  15:31:31 '),(2,10,36,NULL,'de.n-tv','211 ntv text Sa 12.3.   00:17:04 '),(3,10,37,NULL,'de.RTL_II','700 RTL II   Sa 12.3.   00:17:02 '),(4,10,32,NULL,'de.RTL-TEXT','870 RTLtext   Sa 12.3.  16:02:57 '),(5,10,38,NULL,'de.RTL_up','200 RTL up Sa 12.3.     00:17:08 '),(6,10,33,NULL,'de.VOX-TEXT','760 VOX-TEXT Fr 11.3.   15:31:30 '),(7,27,3025,NULL,'de.n-tv','211 ntv text Fr 11.3.   11:14:34 '),(8,27,509,NULL,'at.atv','460 ATV/ATV2  Sa 12.03. 18:41 18 '),(9,27,505,NULL,'at.ORF2','472 ORF2    Fr 11.03.22 11:14:41 '),(10,27,185,NULL,NULL,'640 Teletext   12.03.22 18:42:04 '),(11,27,165,NULL,'at.ORF1','472 ORF1    Sa 12.03.22 03:32 56 '),(12,27,515,NULL,'at.ORF2','472 ORF2    Fr 11.03.22 18:42:08 '),(13,51,2003,NULL,'de.HSE','100 Sachsen1 11.03.22 12:22:29   '),(14,23,65,NULL,NULL,' Fri 11 Mar 2022        09:18:26 '),(15,23,47,NULL,NULL,'                                 '),(16,23,38,NULL,NULL,'100 FAB-TELETEXT 12.03. 00 54:17 '),(17,23,42,NULL,'es.la_2','428  1/1  LA 2 S-12-MAR 02 44 07 '),(18,23,41,NULL,NULL,'800 FAB-TELETEXT 16.09. 03 36:45 '),(19,23,62,NULL,NULL,'800 FAB-TELETEXT 16.09. 03 40:39 '),(20,23,56,NULL,NULL,'800 FAB-TELETEXT 30.08. 07 51:11 '),(21,23,59,NULL,NULL,'                                 '),(22,23,53,NULL,NULL,' Fri 11 Mar 2022        16:44:30 '),(23,18,304,NULL,'de.HR-Text','266 hr-text Fr 11.03.22 17:05:10 '),(24,18,204,NULL,'de.BR','537 BR Text  11.03.2022 09:31:41 '),(25,18,604,NULL,'de.WDR','616 WDR Text  Sa 12.03. 09:31:03 '),(26,18,104,NULL,'de.ARD-Text','484 ARD Text Fr.11.03.  17:05:26 '),(27,18,804,NULL,'de.SWR','642 SWRtext Sa,12.03.22 01:57:28 '),(28,18,504,NULL,'de.BR','537 BR Text  12.03.2022 17:09:15 '),(29,52,520,NULL,'de.nitro','238 NITRO      Fr 11.3. 12:34:39 '),(30,52,320,NULL,'de.SuperRTL','301  SRTL   Fr,11.03.22 12:34:58 '),(31,52,420,NULL,'de.RTL_II','700 RTL II   Sa 12.3.   04:53:45 '),(32,52,120,NULL,'de.RTL-TEXT','770 RTLtext   Sa 12.3.  04:53:32 '),(33,52,220,NULL,'de.VOX-TEXT','760 VOX-TEXT Fr 11.3.   12:34:50 '),(34,45,4115,NULL,'de.RTL-TEXT','870 RTLtext   Fr 11.3.  11:57:00 '),(35,25,32,NULL,NULL,'800 FAB-TELETEXT 04.10. 07:16:06 '),(36,25,56,NULL,NULL,'800 FAB-TELETEXT 15.09. 19:55:08 '),(37,25,53,NULL,NULL,'                                 '),(38,25,62,NULL,NULL,'428  1/1  TDP  V-11-MAR 10 28 21 '),(39,25,68,NULL,NULL,'                                 '),(40,25,41,NULL,NULL,'                                 '),(41,25,65,NULL,NULL,'100 PARAMOUNT  11MAR22  02:03:36 '),(42,25,35,NULL,NULL,'                                 '),(43,25,59,NULL,'es.la_1','428     LA 1   V-11-MAR 17:54:36 '),(44,36,1115,NULL,'at.Servus_TV','348  SERVUS TV   12.03. 11:08:36 '),(45,36,2115,NULL,'at.Servus_TV','348  SERVUS TV   11.03. 18:52:53 '),(46,36,1025,NULL,'de.nitro','238 NITRO      Fr 11.3. 18:52:32 '),(47,36,1013,NULL,'at.ORF_III','413 ORF III Sa.12.03.22 03:42 21 '),(48,29,65,NULL,NULL,'                                 '),(49,29,50,NULL,NULL,'                                 '),(50,29,44,NULL,NULL,'100 FAB-TELETEXT 11.03. 02:51:10 '),(51,39,835,NULL,NULL,'                                 '),(52,26,71,NULL,'es.24h','428  1/1  24h  V-11-MAR 03 34 07 '),(53,26,59,NULL,NULL,'802                              '),(54,26,35,NULL,'es.atresmedia','876  ATRESMEDIA  12 Mar          '),(55,26,62,NULL,NULL,'100 SUBT COSMO OP47 01NO21       '),(56,26,32,NULL,NULL,'888                              '),(57,48,42,NULL,'de.RTL-TEXT','870 RTLtext   Fr 11.3.  12:21:37 '),(58,9,37,NULL,'de.Kabel1_Doku','261  K1Doku  Sa 12 Maerz00:05:17 '),(59,9,36,NULL,'de.ProSiebenMAXX','200 ProSiebenMAXX 12.3. 08:06:46 '),(60,9,34,NULL,'de.kabeleins','200Kabel Eins Fr 11 Mrz 08:02:42 '),(61,9,35,NULL,'de.SIXX','201  sixx.de  Sa 12.3.  08:06:44 '),(62,9,33,NULL,'de.ProSieben','200 ProSieben Fr 11 Mar 15:16:42 '),(63,9,32,NULL,'de.SAT1','200  SAT1.de  Sa 12 Mrz 08:06:36 '),(64,31,35,NULL,NULL,'100CPXTRA 131121                 '),(65,31,4018,NULL,NULL,'888 FAB-TELETEXT 11.03. 03:51:34 '),(66,19,504,NULL,'de.WDR','616 WDR Text  Sa 12.03. 17:23:06 '),(67,19,1204,NULL,'de.ndr','592 NDR Text  Sa.12.03. 02:10:05 '),(68,19,1304,NULL,'de.Saartext',' 272 SAARTEXT Fr. 11.03 17:21:52 '),(69,15,65,NULL,'de.SuperRTL','306  SRTL   Fr,11.03.22 01:12:59 '),(70,15,105,NULL,'de.RTL-TEXT','770 RTLtext   Sa 12.3.  01:13:44 '),(71,15,80,NULL,'de.n-tv','211 ntv text Sa 12.3.   01:13:09 '),(72,15,84,NULL,'de.nitro','238 NITRO      Fr 11.3. 15:56:23 '),(73,15,70,NULL,'de.RTL_up','200 RTL up Sa 12.3.     08:44:06 '),(74,15,71,NULL,'de.VOX-TEXT','760 VOX-TEXT Fr 11.3.   15:56:34 '),(75,15,68,NULL,'de.RTL_II','700 RTL II   Sa 12.3.   08:44:07 '),(76,8,33,NULL,'ch.ProSieben','263 ProSieben.ch 12 Mar 15:21:34 '),(77,8,802,NULL,'at.SAT1','260 SAT1.at  Sa 12 Maerz15:21:27 '),(78,8,38,NULL,'ch.SAT1','201 SAT1.ch  Fr 11 Maerz14:49:04 '),(79,8,39,NULL,'at.PULS_4','300  PULS 4   11.03.22  14:48:08 '),(80,8,36,NULL,'at.ProSieben','200 ProSieben.at 10 Mar 23:21:23 '),(81,8,165,NULL,'ch.kabeleins','231 kabeleins.ch 11 Mrz 07:35:45 '),(82,8,169,NULL,'at.kabeleins','262 kabeleins.at 12 Mrz 07:31:25 '),(83,8,40,NULL,'de.SAT1','100  SAT1.de  Fr 11 Mrz 14:48:13 '),(84,21,167,NULL,'de.QVC-TEXT','614 QVC-TEXT 12.03.2022 02:14 26 '),(85,21,36,NULL,'de.Bibel_TV','300 Bibel TV Sa 12.03. 09:49:31  '),(86,21,146,NULL,'de.QVC-TEXT','614 QVCtext Fr 11.03.22 02:15:41 '),(87,16,403,NULL,'de.RTL_II','700 RTL II   Sa 12.3.   16:44:01 '),(88,16,203,NULL,'de.RTL-TEXT','770 RTLtext   Sa 12.3.  01:24:10 '),(89,16,102,NULL,'de.Eurosport','270 Eurosport Fr. 11.3. 01:23:46 '),(90,16,503,NULL,'de.SuperRTL','301  SRTL   Fr,11.03.22 16:07:09 '),(91,16,603,NULL,'de.VOX-up','207 VOX up   Fr 11.Mar  08:55:56 '),(92,16,303,NULL,'de.VOX-TEXT','760 VOX-TEXT Sa 12.3.   16:44:01 '),(93,16,576,NULL,'de.HSE','557   HSE    12.03.2022 01:24:26 '),(94,5,38,NULL,'de.QVC-TEXT','604 QVCtext Do 10.03.22 21:40:45 '),(95,5,37,NULL,'de.TLC','399  TLC.de    11.03.22 21:56:38 '),(96,5,35,NULL,'de.SIXX','203  sixx.de  Fr 11.3.  06:17:25 '),(97,5,36,NULL,'de.Disney_Channel','423  Disney Sa 12.03.22 13:55:50 '),(98,5,32,NULL,'de.1-2-3.tv','486  1-2-3.tv  12.03.22 05:50:09 '),(99,5,33,NULL,'de.QVC-TEXT','604 QVC-TEXT 10.03.2022 21:40 49 '),(100,5,34,NULL,'de.N24_Doku','200  N24 DOKU Fr 11 Mrz 06:17:24 '),(101,41,6330,NULL,'de.ZDF-neo','312 zdf_neo Fr 11.03.22 04:22:41 '),(102,41,6130,NULL,'de.ZDF','646 ZDFtext Sa 12.03.22 19:19:13 '),(103,1,44,NULL,NULL,'                                 '),(104,1,62,NULL,NULL,'                                 '),(105,1,65,NULL,'es.atresmedia','276  ATRESMEDIA  11 Mar          '),(106,1,47,NULL,NULL,'                                 '),(107,1,41,NULL,NULL,'801                              '),(108,1,32,NULL,NULL,'                                 '),(109,46,1221,NULL,NULL,'                                 '),(110,14,330,NULL,'de.KI.KA','100 KI.KA   Sa 12.03.22 16:15 23 '),(111,14,130,NULL,'de.ZDF','649 ZDFtext Fr 11.03.22 08:27:25 '),(112,14,630,NULL,'de.ZDF-info','632 ZDFinfo Fr 11.03.22 15:43 42 '),(113,14,680,NULL,'de.ZDF-neo','112 zdf_neo Sa 12.03.22 08:31:20 '),(114,14,230,NULL,'de.3sat','430  3satText  12.03.22 08:31:14 '),(115,3,34,NULL,'de.Welt','202     WELT Fr 11 Mrz  12:52:12 '),(116,3,35,NULL,'de.QVC-TEXT','614 QVC-TEXT 11.03.2022 20:38:51 '),(117,3,36,NULL,'de.HSE','556   HSE    11.03.2022 20:38:48 '),(118,22,3804,NULL,'de.WDR','618 WDR Text  Sa 12.03. 10:04:28 '),(119,22,1750,NULL,NULL,'Teletext                         '),(120,32,56,NULL,NULL,'100 SUB.CLAS      DD MM 19:21:19 '),(121,32,35,NULL,NULL,'100 FAB-TELETEXT 15.09. 11:05:02 '),(122,32,65,NULL,NULL,'                                 '),(123,13,3131,NULL,NULL,'                                 '),(124,12,504,NULL,NULL,'640 Teletext   12.03.22 00:19:54 '),(125,12,500,NULL,'de.GermanHealth',' GermanHealth  11.03.22 00:05:40 '),(126,47,2215,NULL,'at.ORF_Sport_plus','253 ORF SPORT+ 11.03.22 04:53 46 '),(127,47,2295,NULL,'de.RTL_up','200 RTL up Fr 11.3.     04:53:29 '),(128,47,2235,NULL,'at.atv','400 ATV/ATV2  Fr 11.03. 19:44:16 '),(129,47,2285,NULL,'at.atv','460 ATV/ATV2  Sa 12.03. 12:08:20 '),(130,47,2245,NULL,'de.Bibel_TV','300 Bibel TV HD 12.03. 04:32:21  '),(131,40,3004,NULL,'de.MDR','576 MDR     Fr 11.03.22 19:05:58 '),(132,40,2904,NULL,'de.MDR','576 MDR     Sa 12.03.22 03:54:04 '),(133,40,604,NULL,'de.RBB-TEXT','273 rbbtext Sa 12.03.22 19:09:04 '),(134,40,2604,NULL,'de.ndr','592 NDR Text  Sa.12.03. 03:55:11 '),(135,40,3104,NULL,'de.SWR','642 SWRtext Fr,11.03.22 04:13:45 '),(136,40,2804,NULL,'de.MDR','576 MDR     Fr 11.03.22 19:05:58 '),(137,7,33,NULL,'de.ProSieben','200 ProSieben Do 10 Mar 22:53:34 '),(138,7,37,NULL,'de.ProSiebenMAXX','200 ProSiebenMAXX 12.3. 14:51:21 '),(139,7,36,NULL,'de.SAT.1_GOLD','200 SAT.1 GOLD  11. Mrz 14:18:08 '),(140,7,35,NULL,'de.Welt','202     WELT Fr 11 Mrz  14:18:00 '),(141,7,41,NULL,'de.Kabel1_Doku','261  K1Doku  Do 10 Maerz22:53:31 '),(142,7,32,NULL,'de.SAT1','100  SAT1.de  Fr 11 Mrz 22:52:58 '),(143,7,34,NULL,'de.kabeleins','200Kabel Eins Fr 11 Mrz 14:18:58 '),(144,35,49,NULL,NULL,'800 FAB-TELETEXT 15.09. 04:48:24 '),(145,35,32,NULL,NULL,'                                 '),(146,35,35,NULL,NULL,'888 FAB-TELETEXT 11.03. 03:52 05 '),(147,35,48,NULL,NULL,'                                 '),(148,35,43,NULL,NULL,'100 FAB-TELETEXT 11.03. 02 02:03 '),(149,24,1055,NULL,NULL,'                                 '),(150,4,35,NULL,'de.Channel21','401  Channel21  12.03. 20:46:25  '),(151,4,45,NULL,'de.DMAX','220  DMAX.de   10.03.22 21:07:16 '),(152,4,33,NULL,'de.TLC','399  TLC.de    12.03.22 20:46:39 '),(153,4,32,NULL,'de.N24_Doku','200  N24 DOKU Fr 11 Mrz 13:03:15 '),(154,44,65,NULL,'es.la_1','428     LA 1   V-11-MAR 19 16 46 '),(155,44,34,NULL,NULL,' Sat 12 Mar 2022        03:07:58 '),(156,44,41,NULL,NULL,'800 FAB-TELETEXT 16.09. 05:13:24 '),(157,30,38,NULL,NULL,'                                 '),(158,30,62,NULL,NULL,'                                 '),(159,30,41,NULL,NULL,'                                 '),(160,2,32,NULL,'de.SKY','100  Sky    Sa. 12. 03. 12:43:21 '),(161,6,39,NULL,'de.Sport1','650 SPORT1 Fr, 11.03.22 13:51:25 '),(162,6,44,NULL,'de.DMAX','220  DMAX.de   12.03.22 14:18:49 '),(163,6,38,NULL,'de.Tele5','300  TELE5 Do 10 Mrz    22:21:59 '),(164,6,37,NULL,'de.HSE','556   HSE    11.03.2022 22:20:00 '),(165,6,40,NULL,'de.Sonnenklar-TV','412/00 Sonnenklar TV06:38:37     ');
/*!40000 ALTER TABLE `text_service` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transponders`
--

DROP TABLE IF EXISTS `transponders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transponders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sat_number` int(11) DEFAULT NULL,
  `delivery_system` varchar(10) DEFAULT NULL,
  `lnb` varchar(25) DEFAULT NULL,
  `frequency` bigint(20) DEFAULT NULL,
  `polarization` varchar(10) DEFAULT NULL,
  `symbol_rate` bigint(20) DEFAULT NULL,
  `modulation` varchar(10) DEFAULT NULL,
  `pilot` varchar(10) DEFAULT NULL,
  `inner_fec` varchar(10) DEFAULT NULL,
  `inversion` varchar(25) DEFAULT NULL,
  `rolloff` varchar(10) DEFAULT NULL,
  `stream_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `transponders_id` (`sat_number`,`frequency`,`polarization`,`symbol_rate`,`stream_id`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transponders`
--

LOCK TABLES `transponders` WRITE;
/*!40000 ALTER TABLE `transponders` DISABLE KEYS */;
INSERT INTO `transponders` VALUES (1,1,'DVBS','EXTENDED',10759000,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(2,1,'DVBS2','EXTENDED',11914500,'HORIZONTAL',27500000,'QPSK','OFF','9/10','AUTO','35',0),(3,1,'DVBS2','EXTENDED',10773250,'HORIZONTAL',22000000,'PSK/8','ON','3/4','AUTO','20',0),(4,1,'DVBS','EXTENDED',12148500,'HORIZONTAL',27500000,NULL,NULL,'3/4','AUTO',NULL,NULL),(5,1,'DVBS','EXTENDED',12460500,'HORIZONTAL',27500000,NULL,NULL,'3/4','AUTO',NULL,NULL),(6,1,'DVBS','EXTENDED',12480000,'VERTICAL',27500000,NULL,NULL,'3/4','AUTO',NULL,NULL),(7,1,'DVBS','EXTENDED',12544750,'HORIZONTAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(8,1,'DVBS','EXTENDED',12051000,'VERTICAL',27500000,NULL,NULL,'3/4','AUTO',NULL,NULL),(9,1,'DVBS2','EXTENDED',11464250,'HORIZONTAL',22000000,'PSK/8','ON','2/3','AUTO','35',0),(10,1,'DVBS2','EXTENDED',10832250,'HORIZONTAL',22000000,'PSK/8','ON','2/3','AUTO','20',0),(11,1,'DVBS2','EXTENDED',11435000,'VERTICAL',22000000,'PSK/8','ON','2/3','AUTO','35',0),(12,1,'DVBS','EXTENDED',12633250,'HORIZONTAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(13,1,'DVBS','EXTENDED',11973000,'VERTICAL',27500000,NULL,NULL,'3/4','AUTO',NULL,NULL),(14,1,'DVBS','EXTENDED',11953500,'HORIZONTAL',27500000,NULL,NULL,'3/4','AUTO',NULL,NULL),(15,1,'DVBS','EXTENDED',12187500,'HORIZONTAL',27500000,NULL,NULL,'3/4','AUTO',NULL,NULL),(16,1,'DVBS','EXTENDED',12226500,'HORIZONTAL',27500000,NULL,NULL,'3/4','AUTO',NULL,NULL),(17,1,'DVBS','EXTENDED',12363050,'VERTICAL',27500000,NULL,NULL,'3/4','AUTO',NULL,NULL),(18,1,'DVBS','EXTENDED',11836500,'HORIZONTAL',27500000,NULL,NULL,'3/4','AUTO',NULL,NULL),(19,1,'DVBS','EXTENDED',12421500,'HORIZONTAL',27500000,NULL,NULL,'3/4','AUTO',NULL,NULL),(20,1,'DVBS','EXTENDED',12515250,'HORIZONTAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(21,1,'DVBS','EXTENDED',12551500,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(22,1,'DVBS','EXTENDED',12603750,'HORIZONTAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(23,1,'DVBS','EXTENDED',11317500,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(24,1,'DVBS','EXTENDED',11597000,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(25,1,'DVBS','EXTENDED',11038000,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(26,1,'DVBS','EXTENDED',11156000,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(27,1,'DVBS','EXTENDED',12692250,'HORIZONTAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(28,1,'DVBS','EXTENDED',11685500,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(29,1,'DVBS','EXTENDED',10979000,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(30,1,'DVBS','EXTENDED',10876500,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(31,1,'DVBS','EXTENDED',11097000,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(32,1,'DVBS','EXTENDED',10788000,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(33,1,'DVBS','EXTENDED',11508500,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(34,1,'DVBS','EXTENDED',10847000,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(35,1,'DVBS2','EXTENDED',10817500,'VERTICAL',22000000,'PSK/8','ON','2/3','AUTO','35',0),(36,1,'DVBS','EXTENDED',12662750,'HORIZONTAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(37,1,'DVBS','EXTENDED',10920750,'HORIZONTAL',22000000,NULL,NULL,'7/8','AUTO',NULL,NULL),(38,1,'DVBS2','EXTENDED',12522000,'VERTICAL',22000000,'PSK/8','ON','2/3','AUTO','35',0),(39,1,'DVBS','EXTENDED',11538000,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(40,1,'DVBS','EXTENDED',12109500,'HORIZONTAL',27500000,NULL,NULL,'3/4','AUTO',NULL,NULL),(41,1,'DVBS2','EXTENDED',11361750,'HORIZONTAL',22000000,'PSK/8','ON','2/3','AUTO','35',0),(42,1,'DVBS2','EXTENDED',11170750,'HORIZONTAL',22000000,'PSK/8','ON','3/4','AUTO','35',0),(43,1,'DVBS2','EXTENDED',11626500,'VERTICAL',22000000,'PSK/8','ON','2/3','AUTO','35',0),(44,1,'DVBS2','EXTENDED',10729000,'VERTICAL',22000000,'PSK/8','ON','2/3','AUTO','35',0),(45,1,'DVBS2','EXTENDED',11214250,'HORIZONTAL',22000000,'PSK/8','ON','2/3','AUTO','35',0),(46,1,'DVBS2','EXTENDED',11229000,'VERTICAL',22000000,'PSK/8','ON','2/3','AUTO','35',0),(47,1,'DVBS','EXTENDED',11243750,'HORIZONTAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(48,1,'DVBS','EXTENDED',11391250,'HORIZONTAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(49,1,'DVBS','EXTENDED',11420750,'HORIZONTAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(50,1,'DVBS','EXTENDED',11611750,'HORIZONTAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(51,1,'DVBS','EXTENDED',11067500,'VERTICAL',22000000,NULL,NULL,'5/6','AUTO',NULL,NULL),(52,1,'DVBS2','EXTENDED',11082250,'HORIZONTAL',22000000,'PSK/8','ON','3/4','AUTO','20',0);
/*!40000 ALTER TABLE `transponders` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-04-06 18:08:10
