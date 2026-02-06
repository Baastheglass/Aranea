import "@/styles/globals.css";
import Head from "next/head";

export default function MyApp({ Component, pageProps }) {
  return (
    <>
      <Head>
        <link rel="icon" type="image/png" href="/aranea.png" />
        <link rel="apple-touch-icon" href="/aranea.png" />
          
      </Head>
      <Component {...pageProps} />
    </>
  );
}


