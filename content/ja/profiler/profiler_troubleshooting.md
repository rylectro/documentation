---
aliases:
- /ja/tracing/profiler/profiler_troubleshooting/
further_reading:
- link: /tracing/troubleshooting
  tag: ドキュメント
  text: APM トラブルシューティング
kind: documentation
title: プロファイラのトラブルシューティング
---

{{< programming-lang-wrapper langs="java,python,go,ruby,dotnet,php,ddprof" >}}
{{< programming-lang lang="java" >}}

## プロファイル検索ページにないプロファイル

プロファイラを設定してもプロファイル検索ページにプロファイルが表示されない場合は、[デバッグモード][1]をオンにし、デバッグファイルと次の情報で[サポートチケットを開いてください][2]。

- オペレーティングシステムのタイプとバージョン (例: Linux Ubuntu 20.04)
- ランタイムのタイプ、バージョン、ベンダー (例: Java OpenJDK 11 AdoptOpenJDK)


## デフォルトの設定からオーバーヘッドを軽減する

デフォルトで設定されているオーバーヘッドを許容できない場合、プロファイラーを使用して最小限のコンフィギュレーション設定をすることができます。最小コンフィギュレーションとデフォルトの違いは以下のとおりです。

- `ThreadSleep`、`ThreadPark`、`JavaMonitorWait` イベントのサンプリングのしきい値が、デフォルトの 100ms から 500ms に増加
- `ObjectAllocationInNewTLAB`、`ObjectAllocationOutsideTLAB`、`ExceptionSample`、`ExceptionCount` イベントが無効化

最小コンフィギュレーションを使用するには、`dd-java-agent` のバージョン `0.70.0` を使用していることを確認し、サービス呼び出しを以下に変更します。

```
java -javaagent:dd-java-agent.jar -Ddd.profiling.enabled=true -Ddd.profiling.jfr-template-override-file=minimal -jar <YOUR_SERVICE>.jar <YOUR_SERVICE_FLAGS>
```

## プロファイラー情報の粒度を増加する

プロファイリングデータの粒度をより細かくするには、`comprehensive` コンフィギュレーションを指定します。この方法を取った場合、さらに細かい粒度のコストでプロファイラーオーバーヘッドが増加することにご留意ください。包括的コンフィギュレーションとデフォルトの違いは以下のとおりです。

- `ThreadSleep`、`ThreadPark`、`JavaMonitorWait` イベントのサンプリングのしきい値が、デフォルトの 100ms から 10ms に減少
- `ObjectAllocationInNewTLAB`、`ObjectAllocationOutsideTLAB`、`ExceptionSample`、`ExceptionCount` イベントが有効化

包括的コンフィギュレーションを使用するには、`dd-trace-java` のバージョン `0.70.0` を使用していることを確認し、サービス呼び出しを以下に変更します。

```
java -javaagent:dd-java-agent.jar -Ddd.profiling.enabled=true -Ddd.profiling.jfr-template-override-file=comprehensive -jar <YOUR_SERVICE>.jar <YOUR_SERVICE_FLAGS>
```

## 割り当てプロファイラーの有効化

Java 15 以下では、割り当てが多いアプリケーションでプロファイラーが圧倒される可能性があるため、割り当てプロファイラーはデフォルトでオフになっています。

割り当てプロファイラーを有効にするには、`-Ddd.profiling.allocation.enabled=true` JVM 設定または `DD_PROFILING_ALLOCATION_ENABLED=true` 環境変数を使用してアプリケーションを起動します。

または、`jfp` [オーバーライドテンプレートファイル](#creating-and-using-a-jfr-template-override-file)で次のイベントを有効にすることもできます。

```
jdk.ObjectAllocationInNewTLAB#enabled=true
jdk.ObjectAllocationOutsideTLAB#enabled=true
```

[オーバーライドテンプレートの使用方法はこちら。](#creating-and-using-a-jfr-template-override-file)

## ヒーププロファイラーの有効化
<div class="alert alert-info">Java ヒーププロファイラー機能はベータ版です。</div>
<div class="aler alert-info">この機能には、Java 11.0.12、15.0.4、16.0.2、17.0.3、または 18 以降が必要です</div>
ヒーププロファイラーを有効にするには、`-Ddd.profiling.heap.enabled=true` JVM 設定または `DD_PROFILING_HEAP_ENABLED=true` 環境変数を使用してアプリケーションを起動します。

または、`jfp` [オーバーライドテンプレートファイル](#creating-and-using-a-jfr-template-override-file)で次のイベントを有効にすることもできます。

```
jdk.OldObjectSample#enabled=true
```

[オーバーライドテンプレートの使用方法はこちら。](#creating-and-using-a-jfr-template-override-file)

## プロファイルからの機密情報の削除

システムプロパティにユーザー名やパスワードなどの機密情報が含まれている場合は、`jdk.InitialSystemProperty` を無効にして `jfp` [オーバーライドテンプレートファイル](#creating-and-using-a-jfr-template-override-file) を作成し、システムプロパティイベントをオフにします。

```
jdk.InitialSystemProperty#enabled=false
```

[オーバーライドテンプレートの使用方法はこちら。](#creating-and-using-a-jfr-template-override-file)

## プロファイラを圧倒する大きな割り当て

割り当てプロファイリングをオフにするには、`jfp` [オーバーライドテンプレートファイル](#creating-and-using-a-jfr-template-override-file)で次のイベントを無効にします。

```
jdk.ObjectAllocationInNewTLAB#enabled=false
jdk.ObjectAllocationOutsideTLAB#enabled=false
```

[オーバーライドテンプレートの使用方法はこちら。](#creating-and-using-a-jfr-template-override-file)

## ガベージコレクターの速度を低下させるメモリリーク検出

メモリリーク検出をオフにするには、`jfp` [オーバーライドテンプレートファイル](#creating-and-using-a-jfr-template-override-file)で次のイベントを無効にします。

```
jdk.OldObjectSample#enabled=false
```

[オーバーライドテンプレートの使用方法はこちら。](#creating-and-using-a-jfr-template-override-file)

## プロファイラを圧倒する例外

Datadog 例外プロファイラは通常の条件下では、フットプリントとオーバーヘッドが小さくなります。ただし、多くの例外が作成されてスローされると、プロファイラに大きなオーバーヘッドが発生することがあります。これは、コントロールフローに例外を使用した場合などに発生する可能性があります。例外率が異常に高い場合は、例外の原因を修正するまで、例外プロファイリングを一時的にオフにします。

例外プロファイリングを無効にするには、`-Ddd.integration.throwables.enabled=false` JVM 設定でトレーサーを開始します。

より一般的な例外率に戻った後は、この設定をオンに戻すことを忘れないでください。

## Java 8 のサポート

次の OpenJDK 8 ベンダーでは、最新バージョンに JDK Flight Recorder が含まれているため、Continuous Profiling がサポートされます。

| ベンダー                      | Flight Recorder を含む JDK バージョン |
| --------------------------- | ----------------------------------------- |
| Azul                        | u212 (u262 推奨)                |
| AdoptOpenJDK                | u262                                      |
| RedHat                      | u262                                      |
| Amazon (Corretto)           | u262                                      |
| Bell-Soft (Liberica)        | u262                                      |
| すべてのベンダーのアップストリームビルド | u272                                      |

ベンダーがリストにない場合は、他のベンダーが開発中またはベータ版サポートに対応している可能性があるため、[サポートチケットを開いてください][2]。

## JFR テンプレートオーバーライドファイルの作成と使用

オーバーライドテンプレートを使用すると、オーバーライドするプロファイリングプロパティを指定できます。ただし、デフォルトでは、オーバーヘッドとデータ密度の間でトレードオフのバランスを程よく保ち、大部分のユースケースに対応できるように設定されています。オーバーライドファイルを使用するには、次のステップを実行します。

1. アクセス可能なディレクトリで、サービスの起動時に `dd-java-agent` を使用して、オーバーライドファイルを作成します。
    ```
    touch dd-profiler-overrides.jfp
    ```

2. 必要なオーバーライドファイルを jfp ファイルに追加します。たとえば、割り当てプロファイリングと JVM システムプロパティを無効にする場合、`dd-profiler-overrides.jfp` ファイルは次のようになります。

    ```
    jdk.ObjectAllocationInNewTLAB#enabled=false
    jdk.ObjectAllocationOutsideTLAB#enabled=false
    jdk.InitialSystemProperty#enabled=false
    ```

3. アプリケーションを `dd-java-agent` で実行している場合は、サービスの起動時に `-Ddd.profiling.jfr-template-override-file=</path/to/override.jfp>` を使用してオーバーライドファイルを指定する必要があります。たとえば、次のようになります。

    ```
    java -javaagent:/path/to/dd-java-agent.jar -Ddd.profiling.enabled=true -Ddd.logs.injection=true -Ddd.profiling.jfr-template-override-file=</path/to/override.jfp> -jar path/to/your/app.jar
    ```

[1]: /ja/tracing/troubleshooting/#tracer-debug-logs
[2]: /ja/help/
{{< /programming-lang >}}
{{< programming-lang lang="python" >}}

## プロファイル検索ページにないプロファイル

プロファイラを設定してもプロファイル検索ページにプロファイルが表示されない場合は、[デバッグモード][1]をオンにし、デバッグファイルと次の情報で[サポートチケットを開いてください][2]。

- オペレーティングシステムのタイプとバージョン (例: Linux Ubuntu 20.04)
- ランタイムのタイプ、バージョン、ベンダー (例: Python 3.9.5)

その他のガイダンスについては、Python APM クライアントの[トラブルシューティングドキュメント][3]を参照してください。

[1]: /ja/tracing/troubleshooting/#tracer-debug-logs
[2]: /ja/help/
[3]: https://ddtrace.readthedocs.io/en/stable/troubleshooting.html
{{< /programming-lang >}}
{{< programming-lang lang="go" >}}

## プロファイル検索ページにないプロファイル

プロファイラを設定してもプロファイル検索ページにプロファイルが表示されない場合は、[デバッグモード][1]をオンにし、デバッグファイルと次の情報で[サポートチケットを開いてください][2]。

- オペレーティングシステムのタイプとバージョン (例: Linux Ubuntu 20.04)
- ランタイムのタイプ、バージョン、ベンダー (例: Go 1.16.5)


[1]: /ja/tracing/troubleshooting/#tracer-debug-logs
[2]: /ja/help/
{{< /programming-lang >}}
{{< programming-lang lang="ruby" >}}

## プロファイル検索ページにないプロファイル

プロファイラを設定してもプロファイル検索ページにプロファイルが表示されない場合は、[デバッグモード][1]をオンにし、デバッグファイルと次の情報で[サポートチケットを開いてください][2]。

- オペレーティングシステムのタイプとバージョン (例: Linux Ubuntu 20.04)
- ランタイムのタイプ、バージョン、ベンダー (例: Ruby 2.7.3)

## アプリケーションが「スタックレベルが深すぎます (SystemStackError)」エラーをトリガーします

この問題は [`dd-trace-rb` バージョン `0.54.0`][3] からは発生しないと思われます。
それでも問題が解決しない場合は、エラーに至るまでのバックトレースを添えて、[サポートチケットを作成][2]してください。

`0.54.0` より前のバージョンでは、プロファイラーはスレッド生成を追跡するために Ruby VM をインスツルメントする必要があり、他の gem による同様のインスツルメンテーションと衝突していました。

以下の gem のいずれかを使用している場合

* `rollbar`: バージョン 3.1.2 以降を使用していることを確認します。
* `logging`: `LOGGING_INHERIT_CONTEXT` 環境変数を `false` に設定して、 `logging` のスレッドコンテキストの継承を
  無効にします。

## レスキュージョブのプロファイルがありません

[Resque][4] のジョブをプロファイリングする場合、[Resque のドキュメント][5]にあるように、`RUN_AT_EXIT_HOOKS` 環境変数を `1` に設定する必要があります。

このフラグがないと、短期間の Resque ジョブのプロファイルは使用できなくなります。

## Ruby VM のジャストインタイムヘッダーのコンパイルに失敗したため、プロファイリングがオンにならない

Ruby 2.7 と古いバージョンの GCC (4.8 以下) の間には、プロファイラに影響を与える非互換性があることが知られています ([アップストリーム Ruby レポート][6]、[`dd-trace-rb` バグレポート][7])。その結果、次のようなエラーメッセージが表示されることがあります: "Your ddtrace installation is missing support for the Continuous Profiler because compilation of the Ruby VM just-in-time header failed. Your C compiler or Ruby VM just-in-time compiler seem to be broken.” (Ruby VM ジャストインタイムヘッダーのコンパイルに失敗したため、あなたの ddtrace インストールには Continuous Profiler のサポートが欠けています。C コンパイラまたは Ruby VM ジャストインタイムコンパイラが壊れているようです。)

これを解決するには、オペレーティングシステムまたは Docker イメージを更新して、GCC のバージョンが v4.8 よりも新しいものになるようにしてください。

この問題についての更なるヘルプは、[サポートにお問い合わせ][2]の上、`DD_PROFILING_FAIL_INSTALL_IF_MISSING_EXTENSION=true gem install ddtrace` と結果の `mkmf.log` ファイルを実行したときの出力を含めてお送りください。

## バックトレースが非常に深い場合、フレームが省略される

Ruby プロファイラーでは、プロファイリングデータを収集する際に、深いバックトレースを切り捨てています。切り捨てられたバックトレースは呼び出し元の関数の一部が欠落しているため、ルートコールフレームにリンクすることが不可能になります。その結果、切り捨てられたバックトレースは `N frames omitted` というフレームにまとめられます。

環境変数 `DD_PROFILING_MAX_FRAMES`、または次のコードで、最大深度を増やすことができます。

```ruby
Datadog.configure do |c|
  c.profiling.advanced.max_frames = 500
end
```

## `dd-trace-rb` 1.11.0+ でネイティブ拡張機能を使用する Ruby gems からの予期しないランタイム失敗やエラー

`dd-trace-rb` 1.11.0 から、プロファイラー "CPU Profiling 2.0" が、Ruby アプリケーションに unix シグナル `SIGPROF` を送ることでデータを集め、よりきめ細かいデータ収集が可能になりました。

`SIGPROF` の送信は一般的なプロファイリング手法であり、ネイティブ拡張機能/ライブラリからのシステムコールがシステムの [`EINTR` エラーコード][8]で中断されることがあります。
まれに、ネイティブ拡張機能またはネイティブ拡張機能から呼び出されたライブラリの `EINTR` エラーコードに対するエラー処理が欠けていたり、不正確な場合があります。

この問題の既知の例として、`mysql2` gem と [8.0.0 より古い][9]バージョンの libmysqlclient を一緒に使用した場合です。影響を受ける libmysqlclient のバージョンは、Ubuntu 18.04 に存在することが知られていますが、20.04 およびそれ以降のリリースには存在しません。この場合、プロファイラーが `mysql2` gem が使用されていることを自動検出し、以下に説明する解決策を自動で適用します。

ネイティブ拡張機能を使用した Ruby gems でランタイム失敗やエラーが発生した場合、`SIGPROF` シグナルを使用しないレガシープロファイラーに戻すことができます。レガシープロファイラーに戻すには、`DD_PROFILING_FORCE_ENABLE_LEGACY` 環境変数を `true` に設定するか、コードで以下を設定します。

```ruby
Datadog.configure do |c|
  c.profiling.advanced.force_enable_legacy_profiler = true
end
```

このような非互換性を見つけたり疑ったりした場合は、[サポートチケット][2]で弊社チームにお知らせください。
そうすることで、Datadog はそれらを自動検出リストに追加し、gem/ライブラリの作者と協力して問題を解決することができます。

[1]: /ja/tracing/troubleshooting/#tracer-debug-logs
[2]: /ja/help/
[3]: https://github.com/DataDog/dd-trace-rb/releases/tag/v0.54.0
[4]: https://github.com/resque/resque
[5]: https://github.com/resque/resque/blob/v2.0.0/docs/HOOKS.md#worker-hooks
[6]: https://bugs.ruby-lang.org/issues/18073
[7]: https://github.com/DataDog/dd-trace-rb/issues/1799
[8]: https://man7.org/linux/man-pages/man7/signal.7.html#:~:text=Interruption%20of%20system%20calls%20and%20library%20functions%20by%20signal%20handlers
[9]: https://bugs.mysql.com/bug.php?id=83109
{{< /programming-lang >}}
{{< programming-lang lang="dotnet" >}}

## プロファイル検索ページにないプロファイル

プロファイラーを構成してもプロファイル検索ページにプロファイルが表示されない場合、OS によって確認すべき点が異なりますので、以下にご紹介します。

{{< tabs >}}

{{% tab "Linux" %}}

1. Agent がインストールされ、動作していることを確認します。

2. ローダーログからプロファイラーが読み込まれたことを確認します。

   1. `/var/log/datadog` フォルダにある `dotnet-native-loader-dotnet-<pid>` のログファイルを開きます。

   2. 最後のほうにある `CorProfiler::Initialize: Continuous Profiler initialized successfully.` を探してください。このメッセージがない場合、アプリケーションの環境変数 `DD_TRACE_DEBUG` を設定して、デバッグログを有効にしてください。

   3. アプリケーションを再起動します。

   4. `/var/log/datadog` フォルダにある `dotnet-native-loader-dotnet-<pid>` のログファイルを開きます。

   5. `#Profiler` エントリーを探してください。

   6. プロファイラーライブラリがロードされていることを確認するため、以下の行をチェックしてください。
      ```
      [...] #Profiler
      [...] PROFILER;{BD1A650D-AC5D-4896-B64F-D6FA25D6B26A};win-x64;.\Datadog.Profiler.Native.dll
      [...] PROFILER;{BD1A650D-AC5D-4896-B64F-D6FA25D6B26A};win-x86;.\Datadog.Profiler.Native.dll
      [...] DynamicDispatcherImpl::LoadConfiguration: [PROFILER] Loading: .\Datadog.Profiler.Native.dll [AbsolutePath=/opt/datadog/linux-x64/./Datadog.Tracer.Native.so]
      [...] [PROFILER] Creating a new DynamicInstance object
      [...] Load: /opt/datadog/linux-x64/./Datadog.Tracer.Native.so
      [...] GetFunction: DllGetClassObject
      [...] GetFunction: DllCanUnloadNow
      ```

3. プロファイルのエクスポート結果を確認します。

   1. ステップ 2.2 でデバッグログを有効にしなかった場合、アプリケーションの `DD_TRACE_DEBUG` 環境変数を `true` に設定し、アプリケーションを再起動します。

   2. `/var/log/datadog` フォルダにある `DD-DotNet-Profiler-Native-<Application Name>-<pid>` のログファイルを開きます。

   3. `libddprof error: Failed to send profile.` エントリーを探します。このメッセージは、Agent にコンタクトできないことを意味します。`DD_TRACE_AGENT_URL` が正しい Agent の URL に設定されていることを確認します。詳細については、[.NET プロファイラーの有効化-構成][1]を参照してください。

   4. もし、`Failed to send profile` というメッセージがない場合は、`The profile was sent. Success?` というエントリーを探します。

      以下のメッセージは、プロファイルの送信に成功したことを意味します。
      ```
      true, Http code: 200
      ```

   5. API キーが無効な場合、403 などのエラーの可能性がありますので、他の HTTP コードを確認してください。

4. CPU または Wall タイムのプロファイルがない場合のみ、スタックウォーク用の Datadog シグナルハンドラーが置き換えられていないことを確認します。

   1. `/var/log/datadog` フォルダにある `DD-DotNet-Profiler-Native-<Application Name>-<pid>` のログファイルを開きます。

   2. この 2 つのメッセージを探してみてください。
      - `Profiler signal handler was replaced again. It will not be restored: the profiler is disabled.`
      - `Fail to restore profiler signal handler.`

   3. これらのメッセージの 1 つが存在する場合、アプリケーションコードまたはサードパーティコードが、Datadog シグナルハンドラーの上に自身のシグナルハンドラーを繰り返し再インストールしていることを意味します。これ以上の衝突を避けるため、CPU と Wall タイムプロファイラーを無効にしています。

   なお、`Profiler signal handler has been replaced. Restoring it.` というメッセージが表示されることがありますが、Datadog のプロファイリングには影響しません。これは、Datadog のシグナルハンドラーが上書きされたときに再インストールされることだけを示しています。

[1]: /ja/profiler/enabling/dotnet/?tab=linux#configuration

{{% /tab %}}

{{% tab "Windows" %}}

デフォルトのプロファイラーログディレクトリは `%ProgramData%\Datadog .NET Tracer\logs\` です。v2.24 以前は、デフォルトのディレクトリは `%ProgramData%\Datadog-APM\logs\DotNet` でした。

1. Agent がインストールされ、起動していること、および Windows サービスパネルに表示されていることを確認します。

2. ローダーログからプロファイラーが読み込まれたことを確認します。

   1. デフォルトのログフォルダから `dotnet-native-loader-<Application Name>-<pid>` のログファイルを開きます。

   2. 最後のほうにある `CorProfiler::Initialize: Continuous Profiler initialized successfully.` を探してください。`initialized successfully` メッセージがない場合、アプリケーションの環境変数 `DD_TRACE_DEBUG` を設定して、デバッグログを有効にしてください。

   3. アプリケーションを再起動します。

   4. デフォルトのログフォルダから `dotnet-native-loader-<Application Name>-<pid>` のログファイルを開きます。

   5. `#Profiler` エントリーを探してください。

   6. プロファイラーライブラリがロードされていることを確認するため、以下の行をチェックしてください。
      ```
      [...] #Profiler
      [...] PROFILER;{BD1A650D-AC5D-4896-B64F-D6FA25D6B26A};win-x64;.\Datadog.Profiler.Native.dll
      [...] PROFILER;{BD1A650D-AC5D-4896-B64F-D6FA25D6B26A};win-x86;.\Datadog.Profiler.Native.dll
      [...] DynamicDispatcherImpl::LoadConfiguration: [PROFILER] Loading: .\Datadog.Profiler.Native.dll [AbsolutePath=C:\Program Files\Datadog\.NET Tracer\win-x64\Datadog.Profiler.Native.dll]
      [...] [PROFILER] Creating a new DynamicInstance object
      [...] Load: C:\Program Files\Datadog\.NET Tracer\win-x64\Datadog.Profiler.Native.dll
      [...] GetFunction: DllGetClassObject
      [...] GetFunction: DllCanUnloadNow
      ```

3. プロファイルのエクスポート結果を確認します。

   1. ステップ 2.2 でデバッグログを有効にしなかった場合、アプリケーションの `DD_TRACE_DEBUG` 環境変数を `true` に設定し、アプリケーションを再起動します。

   2. デフォルトのログフォルダから、`DD-DotNet-Profiler-Native-<Application Name>-<pid>` のログファイルを開きます。

   3. `libddprof error: Failed to send profile.` エントリーを探します。このメッセージは、Agent にコンタクトできないことを意味します。`DD_TRACE_AGENT_URL` が正しい Agent の URL に設定されていることを確認します。詳細については、[.NET プロファイラーの有効化-構成][1]を参照してください。

   4. もし、`Failed to send profile` というメッセージがない場合は、`The profile was sent. Success?` というエントリーを探します。

      以下のメッセージは、プロファイルの送信に成功したことを意味します。
      ```
      true, Http code: 200
      ```

   5. API キーが無効な場合、403 などのエラーの可能性がありますので、他の HTTP コードを確認してください。

[1]: /ja/profiler/enabling/dotnet/?tab=linux#configuration

{{% /tab %}}

{{< /tabs >}}

正しくない場合は、[デバッグモード][1]をオンにして、デバッグファイルと以下の情報を添えて[サポートチケットの発行][2]を行います。
- オペレーティングシステムのタイプとバージョン (例: Windows Server 2019 または Ubuntu 20.04)。
- ランタイムのタイプとバージョン (例: .NET Framework 4.8 または .NET Core 6.0)。
- アプリケーションのタイプ (例: IIS で動作する Web アプリケーション)。


## プロファイラー使用時のオーバーヘッドを削減する

### プロファイラーをマシン全体で有効にする

プロファイラーには、プロファイルされたアプリケーションごとに固定されたオーバーヘッドがあるため、Datadog では、マシンレベルで、またはすべての IIS アプリケーションプールでプロファイラーを有効にすることを推奨しません。プロファイラーが使用するリソース量を削減するためには、以下の方法があります。
- CPU コアを増やすなど、割り当てられたリソースを増やす。
- アプリケーションを直接実行するのではなく、バッチファイルに環境を設定することで、特定のアプリケーションだけをプロファイルする。
- プロファイルされる IIS プールの数を減らす (IIS 10 以降でのみ可能)。
- `DD_PROFILING_WALLTIME_ENABLED=0` の設定により、ウォールタイムプロファイリングを無効にする。

### Linux コンテナ

プロファイラーには固定オーバーヘッドがあります。正確な値は変動する可能性がありますが、この固定コストは、非常に小さなコンテナではプロファイラーの相対的なオーバーヘッドが大きくなる可能性があることを意味します。この状況を避けるため、プロファイラーは 1 コア未満のコンテナでは無効化されます。環境変数 `DD_PROFILING_MIN_CORES_THRESHOLD` に 1 より小さい値を設定することで、1 コアというしきい値をオーバーライドできます。 たとえば、`0.5` という値を設定すると、少なくとも 0.5 コアのあるコンテナでプロファイラーが実行されるようになります。

### プロファイラーを無効にする

APM のトレースも CLR プロファイリング API に依存しているため、.NET プロファイルの収集を停止し、.NET トレースの受信を継続したい場合は、以下の環境変数を設定してプロファイリングのみを無効にしてください。

```
 DD_PROFILING_ENABLED=0 
 CORECLR_ENABLE_PROFILING=1
```

## Linux 上のアプリケーションがハングアップしているため、CPU や Wall タイムがない

Linux でアプリケーションがハングアップするなどして無反応になり、CPU や Wall タイムサンプルが利用できなくなった場合は、以下の手順で対応します。

1. `/var/log/datadog/dotnet` フォルダにある `DD-DotNet-Profiler-Native-<Application Name>-<pid>` のログファイルを開きます。

2. `StackSamplerLoopManager::WatcherLoopIteration - Deadlock intervention still in progress for thread ...` を検索してください。このメッセージがない場合、残りは適用されません。

3. このメッセージが見つかった場合、スタックウォーキングメカニズムがデッドロックに陥っている可能性があることを意味します。この問題を調査するには、アプリケーション内のすべてのスレッドのコールスタックをダンプしてください。例えば、gdb デバッガーでこれを行うには

   1. gdb をインストールします。

   2. 次のコマンドを実行します。
      ```
      gdb -p <process id> -batch -ex "thread apply all bt full" -ex "detach" -ex "quit"
      ```

   3. 得られた出力を [Datadog サポート][2]に送信します。


[1]: /ja/tracing/troubleshooting/#tracer-debug-logs
[2]: /ja/help/
{{< /programming-lang >}}
{{< programming-lang lang="php" >}}

## プロファイル検索ページにないプロファイル

プロファイラーを構成しても、プロファイル検索ページにプロファイルが表示されない場合は、`phpinfo()` 関数を実行します。プロファイラーは `phpinfo()` をフックして診断を実行します。Web サーバーに問題がある場合は、コマンドラインからではなく、Web サーバーから `phpinfo()` を実行すると、各サーバー API (SAPI) を個別に構成することができます。

以下の内容で[サポートチケットを発行][1]します。

- オペレーティングシステムのタイプとバージョン (例: Linux Ubuntu 20.04)
- `phpfo()` の出力。PHP のバージョン、SAPI のタイプ、Datadog ライブラリのバージョン、そしてプロファイラーの診断が含まれます。


[1]: /ja/help/
{{< /programming-lang >}}

{{< programming-lang lang="ddprof" >}}

## プロファイル検索ページにないプロファイル

プロファイラを設定してもプロファイル検索ページにプロファイルが表示されない場合は、[冗長ロギング][1]をオンにし、ログファイルと次の情報で[サポートチケットを開いてください][2]。

- Linux カーネルバージョン (`uname -r`)
- libc バージョン (`ldd --version`)
- `/proc/sys/kernel/perf_event_paranoid` の値
- プロファイラーとアプリケーションの両方の引数を含む完全なコマンドライン

また、必要に応じて、冗長ログを有効にし、以下のセクションを確認することでトラブルシューティングを行うことができます。

### "\<ERROR\> Error calling perfopen on watcher"

このエラーは、通常、プロファイラーを作動させるのに十分な権限がない場合に発生します。最も一般的な理由は、必要なオペレーティングシステムの機能が無効になっており、プロファイリングに失敗することです。これは通常、ホストレベルの構成であり、個々のポッドやコンテナのレベルでは設定できません。

`perf_event_paranoid` が再起動後も持続するように設定することは、分布に依存します。診断の手順として、以下を試してみてください。

```shell
echo 1 | sudo tee /proc/sys/kernel/perf_event_paranoid

```

**注**: これは `/proc/sys/kernel/perf_event_paranoid` オブジェクトが存在し、書き込み可能なマウントネームスペースから実行する必要があります。コンテナ内では、この設定はホストから継承されます。

`perf_event_paranoid` の値をオーバーライドするために使用できる機能は 2 つあります。
- `CAP_SYS_ADMIN`: 多くの権限を追加するので、推奨されない場合があります
- `CAP_PERFMON`: BPF と `perf_event_open` 機能を追加します (Linux v5.8 以降で使用可能)

あまり一般的ではない権限の問題がいくつかあります。
- プロファイラーは、起動時に UID が変更されるプロセスをインスツルメントできないことがあります。これは多くの Web サーバーやデータベースでよくあることです。
- プロファイラーは `perf_event_open()` システムコールに依存していますが、コンテナランタイムによってはこれが許可されない場合があります。そのようなことがあるかどうかは、適切なドキュメントをチェックしてください。
- seccomp のプロファイルの中には `perf_event_open()` を禁止しているものがあります。お使いのシステムでそのような構成が行われている場合、プロファイラーを実行できないことがあります。

### "\<WARNING\> Could not finalize watcher"

この警告は、システムがプロファイラーに十分なロックされたメモリーを割り当てられない場合に発生する可能性があります。この現象は、特定のホストでプロファイラーのインスタンスが多すぎる場合 (多くのコンテナ型サービスが同じホストで個別にインスツルメントされている場合など) によく発生します。この問題は、`mlock()` のメモリ制限を増やすか、インスツルメントされるアプリケーションの数を減らすことで解決できます。

他のプロファイリングツールも同様の制限に寄与する可能性があります。

### "\<WARNING\> Failure to establish connection"

このエラーは、通常、プロファイラーが Datadog Agent に接続できないことを意味します。プロファイラーがアップロードに使用するホスト名とポート番号を特定するには、[コンフィギュレーションロギング][3]を有効にしてください。さらに、エラーメッセージの内容から、使用されるホスト名とポートがリレーされる場合があります。これらの値をお使いの Agent の構成と比較してください。プロファイラーの入力パラメーターとデフォルト値の詳細については、[プロファイラーを有効にする][4]を参照してください。

## プロファイルが空またはまばらである

プロファイルが空であったり ("No CPU time reported")、フレーム数が少なかったりすることがあります。これは、アプリケーションのシンボル化情報が貧弱な場合に発生することがあります。プロファイラーは、インスツルメントされたアプリケーションが CPU 上でスケジュールされている場合にのみ起動します。

プロファイルのルートは、アプリケーション名を括弧で囲んでアノテーションをつけたフレームです。このフレームに大量の CPU 時間が表示され、子フレームがない場合、アプリケーションのプロファイリング忠実度が低い可能性があります。次のようなことを考えてみてください。
- ストリップされたバイナリはシンボルが使用できません。ストリップされていないバイナリや、縮小されていないコンテナイメージを使ってみてください。
- 特定のアプリケーションやライブラリは、そのデバッグパッケージがインストールされていると便利です。これは、リポジトリのパッケージマネージャーなどでインストールされたサービスにも当てはまります。

## 共有ライブラリのロード中のエラー

コンパイル済み言語用の Continuous Profiler を動的ライブラリとして使用している場合、以下のエラーでアプリケーションが起動しないことがあります。

```
error while loading shared libraries: libdd_profiling.so: cannot open shared object file: No such file or directory
```

これは、アプリケーションが `libdd_profiling.so` の依存関係で構築されている場合に発生しますが、依存関係の調整中のランタイムでは見られません。以下のいずれかを実行することで修正できます。

- 静的ライブラリを使用してアプリケーションを再構築。一部の構築システムでは、動的ライブラリと静的ライブラリの選択があいまいなため、`ldd` を使用して `libdd_profiling.so` で結果のバイナリに不要な動的依存関係が含まれるかどうかを確認します。
- 動的リンカーの検索パスでディレクトリの 1 つに `libdd_profiling.so` をコピー。ほとんどの Linux システムで、`ld --verbose | grep SEARCH_DIR | tr -s ' ;' \\n` を実行することでこのディレクトリのリストを獲得できます。

[1]: /ja/tracing/troubleshooting/#tracer-debug-logs
[2]: /ja/help/
[3]: /ja/profiler/enabling/ddprof/?tab=environmentvariables#configuration
[4]: /ja/profiler/enabling/ddprof/
{{< /programming-lang >}}
{{< /programming-lang-wrapper >}}

## その他の参考資料

{{< partial name="whats-next/whats-next.html" >}}