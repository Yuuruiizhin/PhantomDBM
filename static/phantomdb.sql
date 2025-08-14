-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: localhost
-- Tiempo de generación: 09-08-2025 a las 03:20:39
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `phantomdb`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `accesos_previos`
--

CREATE TABLE `accesos_previos` (
  `id_accesos_previos` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `host` varchar(255) NOT NULL,
  `dbuser` varchar(100) NOT NULL,
  `dbpass` varchar(255) NOT NULL,
  `dbname` varchar(100) NOT NULL,
  `fecha_uso` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `empresa`
--

CREATE TABLE `empresa` (
  `id_empresa` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `usuario` varchar(30) NOT NULL,
  `passw` varchar(255) NOT NULL,
  `img` varchar(255) NOT NULL,
  `color_one` varchar(20) NOT NULL,
  `color_two` varchar(20) NOT NULL,
  `color_three` varchar(20) NOT NULL,
  `fecha_adicion` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Volcado de datos para la tabla `empresa`
--

INSERT INTO `empresa` (`id_empresa`, `nombre`, `usuario`, `passw`, `img`, `color_one`, `color_two`, `color_three`, `fecha_adicion`) VALUES
(3, 'Ojo Digitall', 'DigitalEye', 'DigitalEye2025', 'https://media.discordapp.net/attachments/1307158001987092483/1403517659231948862/DigitalEye.png?ex=6897d72e&is=689685ae&hm=a9681c584b250294cf6b4d7584f8ffa7197c3e758f48fb1ea331258ae1b2680f&=&width=886&height=886', '#12b000', '#0d7301', '#7ff571', '2025-08-08 22:56:11'),
(4, 'Mente Criminal', 'MenteCriminal', 'MenteCriminal2025', 'https://media.discordapp.net/attachments/1307158001987092483/1403517659731066880/MenteCriminal.png?ex=6897d72e&is=689685ae&hm=38888047d0496f9d9124aaccc062c1c97a0a26d67e54ac09b1f7f9141124e622&=&width=886&height=886', '#dbdbdb', '#1a1a1a', '#ab0000', '2025-08-08 23:02:50');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `perfil`
--

CREATE TABLE `perfil` (
  `id_perfil` int(11) NOT NULL,
  `id_usuario` int(11) NOT NULL,
  `titulo` varchar(64) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `avatar` varchar(255) DEFAULT NULL,
  `youtube` varchar(255) DEFAULT NULL,
  `x` varchar(255) DEFAULT NULL,
  `instagram` varchar(255) DEFAULT NULL,
  `twitch` varchar(255) DEFAULT NULL,
  `github` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuario`
--

CREATE TABLE `usuario` (
  `id_usuario` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(100) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `fecha_registro` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `accesos_previos`
--
ALTER TABLE `accesos_previos`
  ADD PRIMARY KEY (`id_accesos_previos`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `empresa`
--
ALTER TABLE `empresa`
  ADD PRIMARY KEY (`id_empresa`);

--
-- Indices de la tabla `perfil`
--
ALTER TABLE `perfil`
  ADD PRIMARY KEY (`id_perfil`),
  ADD KEY `id_usuario` (`id_usuario`);

--
-- Indices de la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD PRIMARY KEY (`id_usuario`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `accesos_previos`
--
ALTER TABLE `accesos_previos`
  MODIFY `id_accesos_previos` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `empresa`
--
ALTER TABLE `empresa`
  MODIFY `id_empresa` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `perfil`
--
ALTER TABLE `perfil`
  MODIFY `id_perfil` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `usuario`
--
ALTER TABLE `usuario`
  MODIFY `id_usuario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `accesos_previos`
--
ALTER TABLE `accesos_previos`
  ADD CONSTRAINT `accesos_previos_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id_usuario`) ON DELETE CASCADE;

--
-- Filtros para la tabla `perfil`
--
ALTER TABLE `perfil`
  ADD CONSTRAINT `perfil_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
